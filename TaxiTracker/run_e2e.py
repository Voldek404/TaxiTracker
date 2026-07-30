import os

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "TaxiTracker.test_settings",
)

import django
django.setup()

from django.db import connection
from django.core.management import call_command

connection.ensure_connection()

print("Applying migrations...")
call_command("migrate", interactive=False)

print("Loading fixtures...")
call_command("loaddata", "dump.json")

from django.core.wsgi import get_wsgi_application
from wsgiref.simple_server import make_server

application = get_wsgi_application()

print("Server started on http://127.0.0.1:8000")

httpd = make_server("127.0.0.1", 8000, application)

try:
    httpd.serve_forever()
finally:
    connection.close()