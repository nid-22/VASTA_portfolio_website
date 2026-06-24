import os
import dj_database_url
from .settings import *

DEBUG = False

# Use DATABASE_URL (set automatically by Railway PostgreSQL plugin).
# Falls back to the individual DB_* vars from base settings if not set.
_database_url = os.environ.get('DATABASE_URL')
if _database_url:
    DATABASES = {
        'default': dj_database_url.config(
            default=_database_url,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }

STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# WhiteNoise configuration
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = True
WHITENOISE_COMPRESSION_OFFLINE = True

# Cloudinary credentials (used directly by the Cloudinary SDK in import scripts)
# Images are uploaded via cloudinary.uploader.upload() and URLs stored as plain strings
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': os.environ.get('CLOUDINARY_API_KEY'),
    'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET'),
}