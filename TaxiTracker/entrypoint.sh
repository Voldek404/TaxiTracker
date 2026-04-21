#!/bin/sh

echo "⏳ Waiting for PostgreSQL..."

until pg_isready -h db -U admin -d diploma; do
  sleep 1
done

echo "✅ DB is ready"

python manage.py migrate
python manage.py runserver 0.0.0.0:8000