"""
Basic-Pitch RunPod Serverless Worker
Converts audio to MIDI note events using Spotify's Basic-Pitch model
"""

import runpod
import requests
import tempfile
import os
from basic_pitch.inference import predict
from basic_pitch import ICASSP_2022_MODEL_PATH


def download_audio(url: str) -> str:
    """Download audio file from URL to temporary file"""
    response = requests.get(url, timeout=300)
    response.raise_for_status()

    # Determine file extension from URL or content type
    ext = ".wav"
    if ".mp3" in url.lower():
        ext = ".mp3"
    elif ".flac" in url.lower():
        ext = ".flac"
    elif ".ogg" in url.lower():
        ext = ".ogg"

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
        f.write(response.content)
        return f.name


def handler(event):
    """
    RunPod handler for Basic-Pitch inference

    Input:
        audio_url: URL to audio file
        onset_threshold: (optional) Onset detection threshold (0.0-1.0), default 0.5
        frame_threshold: (optional) Frame detection threshold (0.0-1.0), default 0.3
        minimum_note_length: (optional) Minimum note length in ms, default 58

    Output:
        notes: List of NoteEvent objects {pitch, startTime, duration, velocity}
        note_count: Total number of detected notes
    """
    try:
        input_data = event.get("input", {})
        audio_url = input_data.get("audio_url")

        if not audio_url:
            return {"error": "audio_url is required"}

        # Optional parameters
        onset_threshold = input_data.get("onset_threshold", 0.5)
        frame_threshold = input_data.get("frame_threshold", 0.3)
        minimum_note_length = input_data.get("minimum_note_length", 58)

        # Download audio file
        audio_path = download_audio(audio_url)

        try:
            # Run Basic-Pitch inference
            model_output, midi_data, note_events = predict(
                audio_path,
                onset_threshold=onset_threshold,
                frame_threshold=frame_threshold,
                minimum_note_length=minimum_note_length,
            )

            # Convert note events to serializable format
            notes = []
            for note in note_events:
                notes.append({
                    "pitch": int(note.pitch),
                    "startTime": float(note.start_time_s),
                    "duration": float(note.duration_s),
                    "velocity": int(note.velocity),
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
