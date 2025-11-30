# RunPod Serverless Worker for Basic-Pitch
# Optimized for low-resource CPU inference

FROM python:3.10-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt


# Final stage - minimal runtime image
FROM python:3.10-slim

WORKDIR /app

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Optimize Python for production
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ONNX Runtime optimizations for CPU
ENV OMP_NUM_THREADS=4
ENV OMP_WAIT_POLICY=PASSIVE

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy handler
COPY handler.py .

# Pre-download and cache the model during build
# This makes the model part of the image, reducing startup time
RUN python -c "from basic_pitch import ICASSP_2022_MODEL_PATH; from basic_pitch.inference import Model; Model(ICASSP_2022_MODEL_PATH); print('Model cached successfully')"

# RunPod serverless entrypoint
CMD ["python", "-u", "handler.py"]
