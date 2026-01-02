# Backend Dockerfile for YouTube Miner
# FastAPI backend with Python dependencies
# Build from project root: docker build -f backend/Dockerfile -t youtube-miner-backend .
# Note: Must build from root because Docker cannot access parent directories (../)

FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements file from project root
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies that might be missing
RUN pip install --no-cache-dir --upgrade \
    numpy \
    soundfile \
    librosa \
    yt-dlp

# Copy backend code
COPY backend/ ./backend/

# Copy src code (core pipeline modules) from project root
COPY src/ ./src/

# Copy pytest configuration from project root
COPY pytest.ini .

# Create necessary directories
RUN mkdir -p output backend/runs

# Expose port 8000
EXPOSE 8000

# Set Python path to include project root
ENV PYTHONPATH=/app

# Run the FastAPI application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

