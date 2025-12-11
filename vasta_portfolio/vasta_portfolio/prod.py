"""Production database settings.

This file should define a DATABASES dict used in production. It's strongly
recommended to supply production credentials via environment variables and
not to commit secrets into source control.
"""
import os

DATABASES = {
    'default': {
        'ENGINE': os.environ.get('PROD_DB_ENGINE'),
        'NAME': os.environ.get('PROD_DB_NAME', os.environ.get('RDS_DB_NAME')),
        'USER': os.environ.get('PROD_DB_USER', os.environ.get('RDS_USER')),
        'PASSWORD': os.environ.get('PROD_DB_PASSWORD', os.environ.get('RDS_PASSWORD')),
        'HOST': os.environ.get('PROD_DB_HOST', os.environ.get('RDS_HOST')),
        'PORT': os.environ.get('PROD_DB_PORT', os.environ.get('RDS_PORT', '5432')),
    }
}
