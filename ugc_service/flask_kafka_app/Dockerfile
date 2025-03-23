#ugc_sprint_1/flask_kafka_app/Dockerfile
FROM python:3.10

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app/ app/
COPY tests/ tests/

CMD ["gunicorn", "-w", "4", "-k", "gevent", "-b", "0.0.0.0:8002", "app:create_app()"]
