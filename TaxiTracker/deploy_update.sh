# Выполнить из папки проекта
rsync -avz --delete \
  --exclude venv \
  --exclude __pycache__ \
  --exclude .git \
  --exclude media \
  --exclude "*.sh" \
  --exclude "*.ini" \
  --exclude ".env" \
  ./ django@your_ip:/home/django/app


# Выполнить в терминале на удаленном сервере

cd "/home/django/app"
source venv/bin/activate

pip install -r requirements.txt


export DJANGO_ALLOWED_HOSTS="127.0.0.1,localhost,$SERVER_IP"

python manage.py migrate
python manage.py collectstatic --noinput

sudo systemctl restart uwsgi || true
