"""Feed to Attributeapp command module"""
import sys
from datetime import datetime
from optparse import make_option

from django.utils.html import strip_tags
from django.db.utils import IntegrityError
from django.utils.encoding import smart_str
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.utils.text import truncate_words
from django.template.defaultfilters import slugify
from django.core.management.base import CommandError
from django.core.management.base import LabelCommand

from attributeapp import __version__
from attributeapp.models import Attributetype
from attributeapp.models import Attribute
from attributeapp.managers import PUBLISHED
from attributeapp.signals import disconnect_attributeapp_signals


class Command(LabelCommand):
    """Command object for importing a RSS or Atom
    feed into Attributeapp."""
    help = 'Import a RSS or Atom feed into Attributeapp.'
    label = 'feed url'
    args = 'url'

    option_list = LabelCommand.option_list + (
        make_option('--noautoexcerpt', action='store_false',
                    dest='auto_excerpt', default=True,
                    help='Do NOT generate an excerpt if not present.'),
        make_option('--author', dest='author', default='',
                    help='All imported attributetypes belong to specified author'),
        make_option('--attribute-is-tag', action='store_true',
                    dest='attribute-tag', default=False,
                    help='Store attributes as tags'),
        )
    SITE = Site.objects.get_current()

    def __init__(self):
        """Init the Command and add custom styles"""
        super(Command, self).__init__()
        self.style.TITLE = self.style.SQL_FIELD
        self.style.STEP = self.style.SQL_COLTYPE
        self.style.ITEM = self.style.HTTP_INFO
        disconnect_attributeapp_signals()

    def write_out(self, message, verbosity_level=1):
        """Convenient method for outputing"""
        if self.verbosity and self.verbosity >= verbosity_level:
            sys.stdout.write(smart_str(message))
            sys.stdout.flush()

    def handle_label(self, url, **options):
        try:
            import feedparser
        except ImportError:
            raise CommandError('You need to install the feedparser ' \
                               'module to run this command.')

        self.verbosity = int(options.get('verbosity', 1))
        self.auto_excerpt = options.get('auto_excerpt', True)
        self.default_author = options.get('author')
        self.attribute_tag = options.get('attribute-tag', False)
        if self.default_author:
            try:
                self.default_author = User.objects.get(
                    username=self.default_author)
            except User.DoesNotExist:
                raise CommandError('Invalid username for default author')

        self.write_out(self.style.TITLE(
            'Starting importation of %s to Attributeapp %s:\n' % (url, __version__)))

        feed = feedparser.parse(url)
        self.import_attributetypes(feed.attributetypes)

    def import_attributetypes(self, feed_attributetypes):
        """Import attributetypes"""
        for feed_attributetype in feed_attributetypes:
            self.write_out('> %s... ' % feed_attributetype.title)
            creation_date = datetime(*feed_attributetype.date_parsed[:6])
            slug = slugify(feed_attributetype.title)[:255]

            if Attributetype.objects.filter(creation_date__year=creation_date.year,
                                    creation_date__month=creation_date.month,
                                    creation_date__day=creation_date.day,
                                    slug=slug):
                self.write_out(self.style.NOTICE(
                    'SKIPPED (already imported)\n'))
                continue

            attributes = self.import_attributes(feed_attributetype)
            attributetype_dict = {'title': feed_attributetype.title[:255],
                          'content': feed_attributetype.description,
                          'excerpt': feed_attributetype.get('summary'),
                          'status': PUBLISHED,
                          'creation_date': creation_date,
                          'start_publication': creation_date,
                          'last_update': datetime.now(),
                          'slug': slug}

            if not attributetype_dict['excerpt'] and self.auto_excerpt:
                attributetype_dict['excerpt'] = truncate_words(
                    strip_tags(feed_attributetype.description), 50)
            if self.attribute_tag:
                attributetype_dict['tags'] = self.import_tags(attributes)

            attributetype = Attributetype(**attributetype_dict)
            attributetype.save()
            attributetype.attributes.add(*attributes)
            attributetype.sites.add(self.SITE)

            if self.default_author:
                attributetype.authors.add(self.default_author)
            elif feed_attributetype.get('author_detail'):
                try:
                    user = User.objects.create_user(
                        slugify(feed_attributetype.author_detail.get('name')),
                        feed_attributetype.author_detail.get('email', ''))
                except IntegrityError:
                    user = User.objects.get(
                        username=slugify(feed_attributetype.author_detail.get('name')))
                attributetype.authors.add(user)

            self.write_out(self.style.ITEM('OK\n'))

    def import_attributes(self, feed_attributetype):
        attributes = []
        for cat in feed_attributetype.get('tags', ''):
            attribute, created = Attribute.objects.get_or_create(
                slug=slugify(cat.term), defaults={'title': cat.term})
            attributes.append(attribute)
        return attributes

    def import_tags(self, attributes):
        tags = []
        for cat in attributes:
            if len(cat.title.split()) > 1:
                tags.append('"%s"' % slugify(cat.title).replace('-', ' '))
            else:
                tags.append(slugify(cat.title).replace('-', ' '))
        return ', '.join(tags)