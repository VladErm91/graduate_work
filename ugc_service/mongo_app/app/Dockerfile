FROM python:3.10

WORKDIR /app
ENV PYTHONPATH=/app
ENV MONGO_URL=mongodb://mongodb:27017
ENV DATABASE_NAME=cinema

COPY requirements.txt requirements.txt
RUN  pip install --upgrade pip --no-cache-dir\
    && pip install --root-user-action=ignore -r requirements.txt --no-cache-dir

COPY . .

EXPOSE 8766

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8766"]