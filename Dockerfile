# RunPod Serverless Worker for Basic-Pitch
# Spotify's audio-to-MIDI converter

FROM python:3.10-slim

WORKDIR /app

# Prevent interactive prompts during apt-get install
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy handler
COPY handler.py .

# RunPod serverless entrypoint
CMD ["python", "-u", "handler.py"]
