FROM python:3.11-slim

WORKDIR /app

# Install system deps for pdfplumber
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpoppler-cpp-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data /app/uploads

ENV DB_PATH=/app/data/vat_engine.db
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 3003

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "3003"]
