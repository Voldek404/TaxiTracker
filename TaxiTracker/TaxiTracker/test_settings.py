from .settings import *

# DATABASES = {
#     "default": {
#         "ENGINE": "django.contrib.gis.db.backends.postgis",
#         "NAME": "test_db",
#         "USER": "postgres",
#         "PASSWORD": "postgres",
#         "HOST": "localhost",
#         "PORT": "5432",
#     }
# }
SPATIALITE_LIBRARY_PATH = "/opt/homebrew/lib/mod_spatialite.dylib"

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.spatialite",
        "NAME": "file:e2e?mode=memory&cache=shared",
        "OPTIONS": {"uri": True},
    }
}