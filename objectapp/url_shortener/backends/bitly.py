"""Bit.ly url shortener backend for Objectapp"""
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

try:
    from django_bitly.models import Bittle
except ImportError:
    raise ImproperlyConfigured('django_bitly is not available')

if not getattr(settings, 'BITLY_LOGIN', ''):
    raise ImproperlyConfigured('You have to set a BITLY_LOGIN setting')

if not getattr(settings, 'BITLY_API_KEY', ''):
    raise ImproperlyConfigured('You have to set a BITLY_API_KEY setting')


def backend(gbobject):
    """Bit.ly url shortener backend for Objectapp"""
    bittle = Bittle.objects.bitlify(gbobject)
    return bittle.shortUrl
