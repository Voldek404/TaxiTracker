# Выполнить из папки проекта

rsync -avz --delete --dry-run  \
  --exclude venv \
  --exclude __pycache__ \
  --exclude .git \
  --exclude media \
  ./ django@your_ip:/home/django/app

# Выполнить в терминале на удаленном сервере

mkdir "/home/django/app"
cd "/home/django/app"
python -m venv venv

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

sudo pacman -S --noconfirm base-devel gdal postgis postgresql-libs rsync

sudo systemctl enable postgresql
sudo systemctl start postgresql

sudo -u postgres psql <<EOF || true
DO \$\$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'admin') THEN
      CREATE ROLE admin WITH LOGIN PASSWORD 'password' CREATEDB;
   END IF;
END
\$\$;

DO \$\$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'diploma') THEN
      CREATE DATABASE diploma OWNER admin;
   END IF;
END
\$\$;
EOF

sudo -u postgres psql -d diploma <<EOF || true
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
EOF

export DJANGO_ALLOWED_HOSTS="127.0.0.1,localhost,$SERVER_IP"

python manage.py migrate
python manage.py collectstatic --noinput


cat > $APP_DIR/TaxiTracker_uwsgi.ini <<EOF
[uwsgi]
chdir = /home/django/app
module = TaxiTracker.wsgi:application

virtualenv = /home/django/app/venv
pythonpath = /home/django/app

env = DJANGO_SETTINGS_MODULE=TaxiTracker.settings

master = true
processes = 2

socket = 127.0.0.1:8001

vacuum = true
die-on-term = true
enable-threads = true

logto = /home/django/app/uwsgi.log
EOF

cat > /etc/nginx/nginx.conf <<EOF
worker_processes  1;

events {
    worker_connections 1024;
}

http {
    include       mime.types;
    default_type  application/octet-stream;

    sendfile on;
    keepalive_timeout 65;

    upstream django {
        server 127.0.0.1:8001;
    }

    server {
        listen 80;
        server_name $SERVER_IP;

        charset utf-8;
        client_max_body_size 75M;

        location /static/ {
            alias /home/django/app/static/;
        }

        location /media/ {
            alias /home/django/app/media/;
        }

        location / {
            include uwsgi_params;
            uwsgi_pass 127.0.0.1:8001;
        }
    }
}
EOF


sudo systemctl restart postgresql
sudo systemctl restart nginx || true
sudo systemctl restart uwsgi || true

