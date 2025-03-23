FROM python:3.10

WORKDIR /opt/src
ENV PYTHONPATH=/opt/src

COPY requirements.txt requirements.txt
RUN  pip install --upgrade pip --no-cache-dir\
     && pip install -r requirements.txt --no-cache-dir

COPY . .
