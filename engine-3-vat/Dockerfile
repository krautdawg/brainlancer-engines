FROM python:3.11-slim

WORKDIR /app

# Install system deps for pdfplumber
RUN apt-get update && apt-get install -y \
    libpoppler-cpp-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create directory for uploads/temp files
RUN mkdir -p /app/uploads

EXPOSE 3003

ENV APP_PASSWORD=brainlancer2026 \
    DB_PATH=/app/data/vat_engine.db \
    DEMO_QUARTER=1 \
    DEMO_YEAR=2024

# Ensure data directory exists at runtime
CMD ["sh", "-c", "mkdir -p /app/data && uvicorn app:app --host 0.0.0.0 --port 3003"]
