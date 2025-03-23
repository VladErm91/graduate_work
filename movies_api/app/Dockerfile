FROM python:3.10

WORKDIR /opt/app
ENV PYTHONPATH=/opt/app

COPY requirements.txt requirements.txt
RUN  pip install --upgrade pip --no-cache-dir\
     && pip install -r requirements.txt --no-cache-dir
     
COPY . .
