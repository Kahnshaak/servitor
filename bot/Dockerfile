# Multi-arch build: this image is built on the main server and pushed to the Pi.
# Build for ARM64 (Raspberry Pi 4/5): docker buildx build --platform linux/arm64 -t servitor-bot .
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Stateless — no volumes. All config via environment variables.
CMD ["python", "main.py"]
