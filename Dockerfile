FROM python:3.10-slim

WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure instance directory exists for SQLite
RUN mkdir -p instance

EXPOSE 5000

ENV FLASK_APP=run.py
ENV FLASK_DEBUG=1

CMD ["flask", "run", "--host=0.0.0.0"]
