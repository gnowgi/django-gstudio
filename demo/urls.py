"""Urls for the demo of Gstudio"""
from django.conf import settings
from django.contrib import admin
from django.conf.urls.defaults import url
from django.conf.urls.defaults import include
from django.conf.urls.defaults import patterns

from gstudio.sitemaps import TagSitemap
from gstudio.sitemaps import NodetypeSitemap
from gstudio.sitemaps import MetatypeSitemap
from gstudio.sitemaps import AuthorSitemap
from objectapp.sitemaps import GbobjectSitemap



admin.autodiscover()
handler500 = 'demo.views.server_error'
handler404 = 'django.views.defaults.page_not_found'

urlpatterns = patterns(
    '',
    (r'^$', 'django.views.generic.simple.redirect_to',
     {'url': '/gstudio/'}),
    url(r'^gstudio/', include('gstudio.urls')),
    url(r'^objects/', include('objectapp.urls')),
    url(r'^gstudio/objects/', include('objectapp.urls')),
    url(r'^comments/', include('django.contrib.comments.urls')),
    url(r'^xmlrpc/$', 'django_xmlrpc.views.handle_xmlrpc'),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^objects/admin/', include(admin.site.urls)),
    url(r'^gstudio/admin/', include(admin.site.urls)),
    url(r'^gstudio/objects/admin/', include(admin.site.urls)),
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^accounts/', include('registration.urls')),
    url(r'^$', 'django.views.generic.simple.redirect_to',
            { 'template': 'index.html' }, 'index'),
    )

sitemaps = {'tags': TagSitemap,
            'blog': NodetypeSitemap,
            'authors': AuthorSitemap,
            'objecttypes': MetatypeSitemap,
            'gbobjects': NodetypeSitemap}

urlpatterns += patterns(
    'django.contrib.sitemaps.views',
    url(r'^sitemap.xml$', 'index',
        {'sitemaps': sitemaps}),
    url(r'^sitemap-(?P<section>.+)\.xml$', 'sitemap',
        {'sitemaps': sitemaps}),
    )

urlpatterns += patterns(
    '',
    url(r'^404/$', 'django.views.defaults.page_not_found'),
    url(r'^500/$', 'demo.views.server_error'),
    )

if settings.DEBUG:
    urlpatterns += patterns(
        '',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT})
        )
