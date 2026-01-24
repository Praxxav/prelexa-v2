FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y \
    curl \
    libatomic1 \
    && rm -rf /var/lib/apt/lists/*


# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install prisma

# Copy application code
COPY . .

# Make app importable
ENV PYTHONPATH=/app

EXPOSE 8000

# Pre-download TrOCR model during build to ensure offline capability at runtime
RUN python -c "from transformers import TrOCRProcessor, VisionEncoderDecoderModel; \
    TrOCRProcessor.from_pretrained('microsoft/trocr-base-handwritten'); \
    VisionEncoderDecoderModel.from_pretrained('microsoft/trocr-base-handwritten')"

# Run Prisma generate + FastAPI
CMD sh -c "python -m prisma generate --schema prisma/schema.prisma && \
    uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"
