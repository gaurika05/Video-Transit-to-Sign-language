FROM python:3.11-slim

# Install system dependencies and build tools
RUN apt-get update && apt-get install -y \
    ffmpeg \
    gcc \
    g++ \
    python3-dev \
    build-essential \
    curl \
    libffi-dev \
    python3.11-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip

# Install FastAPI without uvicorn[standard] to avoid httptools
RUN pip install --no-cache-dir \
    fastapi==0.68.2 \
    uvicorn==0.15.0 \
    python-multipart==0.0.5 \
    pydantic==1.10.15

# Install remaining dependencies
RUN pip install --no-cache-dir \
    opencv-python-headless==4.5.5.64 \
    numpy==1.22.4 \
    supabase==0.5.8 \
    openai-whisper \
    ffmpeg-python==0.2.0 \
    python-dotenv==0.19.2 \
    slowapi==0.1.9 \
    youtube-transcript-api==0.6.3

# Copy application code
COPY . .

# Create a non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 