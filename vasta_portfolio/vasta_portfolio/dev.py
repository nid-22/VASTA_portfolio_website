"""Development database settings.

This file should define a DATABASES dict used for local development.
Values can be overridden with environment variables if desired.
"""
import os

DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DEV_DB_ENGINE', 'django.db.backends.postgresql'),
        'NAME': os.environ.get('DEV_DB_NAME'),
        'USER': os.environ.get('DEV_DB_USER'),
        'PASSWORD': os.environ.get('DEV_DB_PASSWORD'),
        'HOST': os.environ.get('DEV_DB_HOST'),
        'PORT': os.environ.get('DEV_DB_PORT'),
    }
}
