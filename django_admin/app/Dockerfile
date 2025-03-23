FROM python:3.10

WORKDIR /opt/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV UWSGI_PROCESSES 1
ENV UWSGI_THREADS 16
ENV UWSGI_HARAKIRI 240
ENV DJANGO_SETTINGS_MODULE 'config.settings'


COPY requirements.txt requirements.txt
COPY uwsgi/uwsgi.ini uwsgi.ini

RUN  pip install --upgrade pip \ 
     && pip install -r requirements.txt --no-cache

COPY . .

RUN chmod +x run_uwsgi.sh && mkdir /opt/app/static && mkdir /opt/app/uploads

EXPOSE 8081


#ENTRYPOINT ["uwsgi", "--strict", "--ini", "uwsgi.ini"]
ENTRYPOINT ["/opt/app/run_uwsgi.sh"]