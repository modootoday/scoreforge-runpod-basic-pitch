"""
Basic-Pitch RunPod Serverless Worker
Converts audio to MIDI note events using Spotify's Basic-Pitch model

Optimizations:
- Model pre-loading at startup (eliminates cold start latency)
- ONNX runtime for efficient CPU inference
- Streaming downloads to reduce memory usage
"""

import runpod
import requests
import tempfile
import os
from basic_pitch.inference import predict, Model
from basic_pitch import ICASSP_2022_MODEL_PATH

# Pre-load model at startup to avoid cold start latency
# This runs once when the container starts, not per-request
print("Loading Basic-Pitch model...")
BASIC_PITCH_MODEL = Model(ICASSP_2022_MODEL_PATH)
print("Model loaded successfully!")


def download_audio(url: str) -> str:
    """
    Download audio file from URL to temporary file.
    Uses streaming to reduce memory usage for large files.
    """
    # Stream download to handle large files efficiently
    with requests.get(url, timeout=300, stream=True) as response:
        response.raise_for_status()

        # Determine file extension from URL
        ext = ".wav"
        url_lower = url.lower()
        if ".mp3" in url_lower:
            ext = ".mp3"
        elif ".flac" in url_lower:
            ext = ".flac"
        elif ".ogg" in url_lower:
            ext = ".ogg"
        elif ".m4a" in url_lower:
            ext = ".m4a"

        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
            # Stream in chunks to avoid loading entire file into memory
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
            return f.name


def handler(event):
    """
    RunPod handler for Basic-Pitch inference

    Input:
        audio_url: URL to audio file
        onset_threshold: (optional) Onset detection threshold (0.0-1.0), default 0.5
        frame_threshold: (optional) Frame detection threshold (0.0-1.0), default 0.3
        minimum_note_length: (optional) Minimum note length in ms, default 58
        minimum_frequency: (optional) Minimum note frequency in Hz
        maximum_frequency: (optional) Maximum note frequency in Hz

    Output:
        notes: List of NoteEvent objects {pitch, startTime, duration, velocity}
        note_count: Total number of detected notes
    """
    try:
        input_data = event.get("input", {})
        audio_url = input_data.get("audio_url")

        if not audio_url:
            return {"error": "audio_url is required"}

        # Optional parameters with sensible defaults
        onset_threshold = input_data.get("onset_threshold", 0.5)
        frame_threshold = input_data.get("frame_threshold", 0.3)
        minimum_note_length = input_data.get("minimum_note_length", 58)
        minimum_frequency = input_data.get("minimum_frequency")
        maximum_frequency = input_data.get("maximum_frequency")

        # Download audio file
        audio_path = download_audio(audio_url)

        try:
            # Build predict kwargs
            predict_kwargs = {
                "onset_threshold": onset_threshold,
                "frame_threshold": frame_threshold,
                "minimum_note_length": minimum_note_length,
            }

            # Add frequency filters if provided
            if minimum_frequency is not None:
                predict_kwargs["minimum_frequency"] = minimum_frequency
            if maximum_frequency is not None:
                predict_kwargs["maximum_frequency"] = maximum_frequency

            # Run Basic-Pitch inference with pre-loaded model
            model_output, midi_data, note_events = predict(
                audio_path,
                BASIC_PITCH_MODEL,  # Use pre-loaded model
                **predict_kwargs,
            )

            # Convert note events to serializable format
            # note_events format: [start_time, end_time, note_number, amplitude]
            notes = []
            for note in note_events:
                start_time = float(note[0])
                end_time = float(note[1])
                pitch = int(note[2])
                velocity = int(note[3])  # amplitude already scaled to MIDI velocity

                notes.append({
                    "pitch": pitch,
                    "startTime": start_time,
                    "duration": end_time - start_time,
                    "velocity": velocity,
                })

            return {
                "notes": notes,
                "note_count": len(notes),
            }

        finally:
            # Clean up temporary file
            if os.path.exists(audio_path):
                os.unlink(audio_path)

    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to download audio: {str(e)}"}
    except Exception as e:
        return {"error": f"Inference failed: {str(e)}"}


if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
