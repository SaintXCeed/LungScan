# ── Base image ─────────────────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# System dependencies required by TensorFlow
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
  && rm -rf /var/lib/apt/lists/*

# ── Python dependencies ────────────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# ── Application code ───────────────────────────────────────────────────────────
COPY . .

EXPOSE 8000

# Railway injects $PORT; fallback ke 8000 untuk lokal
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
