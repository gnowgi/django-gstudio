"""Settings for testing objectapp"""
import os
from objectapp.xmlrpc import OBJECTAPP_XMLRPC_METHODS

DATABASES = {'default': {'NAME': 'objectapp_tests.db',
                         'ENGINE': 'django.db.backends.sqlite3'}}

SITE_ID = 1

STATIC_URL = '/static/'

ROOT_URLCONF = 'objectapp.tests.urls'

TEMPLATE_CONTEXT_PROCESSORS = [
    'django.core.context_processors.request',
    'objectapp.context_processors.version']

TEMPLATE_LOADERS = [
    ['django.template.loaders.cached.Loader', [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader']
     ]
    ]

TEMPLATE_DIRS = [os.path.join(os.path.dirname(__file__),
                              'tests', 'templates')]

INSTALLED_APPS = ['django.contrib.contenttypes',
                  'django.contrib.comments',
                  'django.contrib.sessions',
                  'django.contrib.sites',
                  'django.contrib.admin',
                  'django.contrib.auth',
                  'django_xmlrpc',
                  'mptt', 'tagging', 'objectapp']

OBJECTAPP_PAGINATION = 3

XMLRPC_METHODS = OBJECTAPP_XMLRPC_METHODS
