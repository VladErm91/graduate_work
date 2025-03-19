# docker exec fastapi-solution-django_admin-1 python manage.py makemigrations 
# docker exec fastapi-solution-django_admin-1 python manage.py migrate

# docker exec fastapi-solution-django_admin-1 python manage.py createsuperuser \
#         --noinput \

python -m pip install --upgrade pip 
pip install -r auth/requirements.txt
pip install -r django/app/requirements.txt
pip install -r fastapi-solution/app/requirements.txt
pip install -r fastapi-solution/file_api/requirements.txt