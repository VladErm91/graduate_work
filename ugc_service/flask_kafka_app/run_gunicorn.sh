#!/usr/bin/env bash

gunicorn main:app --bind 0.0.0.0:8000 --workers 4 --access-logfile - --error-logfile -