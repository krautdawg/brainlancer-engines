FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p templates

EXPOSE 3004

ENV APP_PASSWORD=brainlancer2026
ENV SECRET_KEY=change-me-in-production

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "3004"]
