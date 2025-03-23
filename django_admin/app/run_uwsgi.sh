#!/usr/bin/env bash

set -e

python manage.py collectstatic --no-input
# python manage.py migrate --fake-initial

uwsgi --strict --ini uwsgi.ini