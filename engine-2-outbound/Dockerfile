FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create templates directory (already there, but ensure)
RUN mkdir -p templates

EXPOSE 3002

ENV APP_PASSWORD=brainlancer2026
ENV DB_PATH=/data/engine2.db

# Data volume for SQLite persistence
VOLUME ["/data"]

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "3002"]
