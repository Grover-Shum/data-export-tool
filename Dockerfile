FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY src/web/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ /app/src/

RUN mkdir -p /tmp/data_export_temp

EXPOSE $PORT

ENV PYTHONUNBUFFERED=1
ENV PORT=8000

CMD ["python", "src/web/run_server.py"]
