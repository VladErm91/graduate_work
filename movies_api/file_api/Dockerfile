FROM python:3.10

WORKDIR /opt/file_api
ENV PYTHONPATH=/opt/file_api

COPY requirements.txt requirements.txt

RUN  pip install --upgrade pip \ 
     && pip install -r requirements.txt --no-cache

COPY . .
