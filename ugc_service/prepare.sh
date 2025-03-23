# docker exec fastapi-solution-django_admin-1 python manage.py makemigrations 
# docker exec fastapi-solution-django_admin-1 python manage.py migrate

# docker exec fastapi-solution-django_admin-1 python manage.py createsuperuser \
#         --noinput \

python -m pip install --upgrade pip 
pip install -r etl/requirements.txt
pip install -r flask-kafka-app/requirements.txt