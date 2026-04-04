FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data

ENV DB_PATH=/app/data/supplier_engine.db
ENV APP_PASSWORD=brainlancer2026

EXPOSE 3005

CMD ["python", "app.py"]
