# Stage 1: build dependencies (includes gcc/musl/rust for compiled packages like pydantic-core)
# These build tools do NOT ship in the final image.
FROM python:3.12-alpine AS builder

WORKDIR /build

RUN apk add --no-cache gcc musl-dev libffi-dev

COPY requirements.txt .
# Install into an isolated prefix so we can copy just the packages to stage 2
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# Stage 2: minimal runtime image — only the installed packages, no build tools
FROM python:3.12-alpine

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy bot source — stateless, all config via environment variables
COPY . .

CMD ["python", "main.py"]
