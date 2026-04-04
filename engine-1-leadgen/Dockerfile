FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directory for SQLite
RUN mkdir -p /data

ENV DB_PATH=/data/leadgen.db
ENV PORT=3001

EXPOSE 3001

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "3001"]
