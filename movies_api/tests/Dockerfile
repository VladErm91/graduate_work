FROM python:3.10

WORKDIR /opt/tests
ENV PYTHONPATH=/opt/tests

COPY requirements.txt requirements.txt
RUN  pip install --upgrade pip --no-cache-dir\
     && pip install --root-user-action=ignore -r requirements.txt --no-cache-dir

COPY . .