import os
import dj_database_url
from .settings import *

DEBUG = False

# Railway provides DATABASE_URL automatically when PostgreSQL plugin is added
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )
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