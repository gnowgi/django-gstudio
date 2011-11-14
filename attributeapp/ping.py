"""Pings utilities for Attributeapp"""
import socket
import xmlrpclib
import threading
from urllib2 import urlopen
from urlparse import urlsplit
from logging import getLogger

from BeautifulSoup import BeautifulSoup

from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse

from attributeapp.settings import PROTOCOL


class URLRessources(object):
    """Object defining the ressources of the website"""

    def __init__(self):
        self.current_site = Site.objects.get_current()
        self.site_url = '%s://%s' % (PROTOCOL, self.current_site.domain)
        self.blog_url = '%s%s' % (self.site_url,
                                  reverse('attributeapp_attributetype_archive_index'))
        self.blog_feed = '%s%s' % (self.site_url,
                                   reverse('attributeapp_attributetype_latest_feed'))


class DirectoryPinger(threading.Thread):
    """Threaded Directory Pinger"""

    def __init__(self, server_name, attributetypes, timeout=10, start_now=True):
        self.results = []
        self.timeout = timeout
        self.attributetypes = attributetypes
        self.server_name = server_name
        self.server = xmlrpclib.ServerProxy(self.server_name)
        self.ressources = URLRessources()

        threading.Thread.__init__(self)
        if start_now:
            self.start()

    def run(self):
        """Ping attributetypes to a Directory in a Thread"""
        logger = getLogger('attributeapp.ping.directory')
        socket.setdefaulttimeout(self.timeout)
        for attributetype in self.attributetypes:
            reply = self.ping_attributetype(attributetype)
            self.results.append(reply)
            logger.info('%s : %s' % (self.server_name, reply['message']))
        socket.setdefaulttimeout(None)

    def ping_attributetype(self, attributetype):
        """Ping an attributetype to a Directory"""
        attributetype_url = '%s%s' % (self.ressources.site_url,
                              attributetype.get_absolute_url())
        attributes = '|'.join([c.title for c in attributetype.attributes.all()])

        try:
            reply = self.server.weblogUpdates.extendedPing(
                self.ressources.current_site.name,
                self.ressources.blog_url, attributetype_url,
                self.ressources.blog_feed, attributes)
        except Exception:
            try:
                reply = self.server.weblogUpdates.ping(
                    self.ressources.current_site.name,
                    self.ressources.blog_url, attributetype_url,
                    attributes)
            except Exception:
                reply = {'message': '%s is an invalid directory.' % \
                         self.server_name,
                         'flerror': True}
        return reply


class ExternalUrlsPinger(threading.Thread):
    """Threaded ExternalUrls Pinger"""

    def __init__(self, attributetype, timeout=10, start_now=True):
        self.results = []
        self.attributetype = attributetype
        self.timeout = timeout
        self.ressources = URLRessources()
        self.attributetype_url = '%s%s' % (self.ressources.site_url,
                                   self.attributetype.get_absolute_url())

        threading.Thread.__init__(self)
        if start_now:
            self.start()

    def run(self):
        """Ping external URLS in a Thread"""
        logger = getLogger('attributeapp.ping.external_urls')
        socket.setdefaulttimeout(self.timeout)

        external_urls = self.find_external_urls(self.attributetype)
        external_urls_pingable = self.find_pingback_urls(external_urls)

        for url, server_name in external_urls_pingable.items():
            reply = self.pingback_url(server_name, url)
            self.results.append(reply)
            logger.info('%s : %s' % (url, reply))

        socket.setdefaulttimeout(None)

    def is_external_url(self, url, site_url):
        """Check of the url in an external url"""
        url_splitted = urlsplit(url)
        if not url_splitted.netloc:
            return False
        return url_splitted.netloc != urlsplit(site_url).netloc

    def find_external_urls(self, attributetype):
        """Find external urls in an attributetype"""
        soup = BeautifulSoup(attributetype.html_content)
        external_urls = [a['href'] for a in soup.findAll('a')
                         if self.is_external_url(
                             a['href'], self.ressources.site_url)]
        return external_urls

    def find_pingback_href(self, content):
        """Try to find Link markup to pingback url"""
        soup = BeautifulSoup(content)
        for link in soup.findAll('link'):
            dict_attr = dict(link.attrs)
            if 'rel' in dict_attr and 'href' in dict_attr:
                if dict_attr['rel'].lower() == 'pingback':
                    return dict_attr.get('href')

    def find_pingback_urls(self, urls):
        """Find the pingback urls of each urls"""
        pingback_urls = {}

        for url in urls:
            try:
                page = urlopen(url)
                headers = page.info()

                if 'text/' not in headers.get('Content-Type', '').lower():
                    continue

                server_url = headers.get('X-Pingback')
                if not server_url:
                    server_url = self.find_pingback_href(page.read())

                if server_url:
                    server_url_splitted = urlsplit(server_url)
                    if not server_url_splitted.netloc:
                        url_splitted = urlsplit(url)
                        server_url = '%s://%s%s' % (url_splitted.scheme,
                                                    url_splitted.netloc,
                                                    server_url)
                    pingback_urls[url] = server_url
            except IOError:
                pass
        return pingback_urls

    def pingback_url(self, server_name, target_url):
        """Do a pingback call for the target url"""
        try:
            server = xmlrpclib.ServerProxy(server_name)
            reply = server.pingback.ping(self.attributetype_url, target_url)
        except (xmlrpclib.Error, socket.error):
            reply = '%s cannot be pinged.' % target_url
        return reply
