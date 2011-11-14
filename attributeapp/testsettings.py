"""Settings for testing attributeapp"""
import os
from attributeapp.xmlrpc import ATTRIBUTEAPP_XMLRPC_METHODS

DATABASES = {'default': {'NAME': 'attributeapp_tests.db',
                         'ENGINE': 'django.db.backends.sqlite3'}}

SITE_ID = 1

STATIC_URL = '/static/'

ROOT_URLCONF = 'attributeapp.tests.urls'

TEMPLATE_CONTEXT_PROCESSORS = [
    'django.core.context_processors.request',
    'attributeapp.context_processors.version']

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
                  'mptt', 'tagging', 'attributeapp']

ATTRIBUTEAPP_PAGINATION = 3

XMLRPC_METHODS = ATTRIBUTEAPP_XMLRPC_METHODS
