"""WordPress to Attributeapp command module"""
import sys
from datetime import datetime
from optparse import make_option
from xml.etree import ElementTree as ET

from django.utils.html import strip_tags
from django.db.utils import IntegrityError
from django.utils.encoding import smart_str
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.utils.text import truncate_words
from django.template.defaultfilters import slugify
from django.contrib import comments
from django.core.management.base import CommandError
from django.core.management.base import LabelCommand

from tagging.models import Tag

from attributeapp import __version__
from attributeapp.models import Attributetype
from attributeapp.models import Attribute
from attributeapp.signals import disconnect_attributeapp_signals
from attributeapp.managers import DRAFT, HIDDEN, PUBLISHED

WP_NS = 'http://wordpress.org/export/%s/'


class Command(LabelCommand):
    """Command object for importing a WordPress blog
    into Attributeapp via a WordPress eXtended RSS (WXR) file."""
    help = 'Import a Wordpress blog into Attributeapp.'
    label = 'WXR file'
    args = 'wordpress.xml'

    option_list = LabelCommand.option_list + (
        make_option('--noautoexcerpt', action='store_false',
                    dest='auto_excerpt', default=True,
                    help='Do NOT generate an excerpt if not present.'),
        make_option('--author', dest='author', default='',
                    help='All imported attributetypes belong to specified author'),
        make_option('--wxr_version', dest='wxr_version', default='1.0',
                    help='Wordpress XML export version'),
        )

    SITE = Site.objects.get_current()
    REVERSE_STATUS = {'pending': DRAFT,
                      'draft': DRAFT,
                      'auto-draft': DRAFT,
                      'inherit': DRAFT,
                      'publish': PUBLISHED,
                      'future': PUBLISHED,
                      'trash': HIDDEN,
                      'private': PUBLISHED}

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

    def handle_label(self, wxr_file, **options):
        global WP_NS
        self.verbosity = int(options.get('verbosity', 1))
        self.auto_excerpt = options.get('auto_excerpt', True)
        WP_NS = WP_NS % options.get('wxr_version')
        self.default_author = options.get('author')
        if self.default_author:
            try:
                self.default_author = User.objects.get(
                    username=self.default_author)
            except User.DoesNotExist:
                raise CommandError('Invalid username for default author')

        self.write_out(self.style.TITLE(
            'Starting migration from Wordpress to Attributeapp %s:\n' % __version__))

        tree = ET.parse(wxr_file)

        self.authors = self.import_authors(tree)

        self.attributes = self.import_attributes(
            tree.findall('channel/{%s}attribute' % WP_NS))

        self.import_tags(tree.findall('channel/{%s}tag' % WP_NS))

        self.import_attributetypes(tree.findall('channel/item'))

    def import_authors(self, tree):
        """Retrieve all the authors used in posts
        and convert it to new or existing user, and
        return the convertion"""
        self.write_out(self.style.STEP('- Importing authors\n'))

        post_authors = set()
        for item in tree.findall('channel/item'):
            post_type = item.find('{%s}post_type' % WP_NS).text
            if post_type == 'post':
                post_authors.add(item.find(
                    '{http://purl.org/dc/elements/1.1/}creator').text)

        self.write_out('%i authors found.\n' % len(post_authors))

        authors = {}
        for post_author in post_authors:
            if self.default_author:
                authors[post_author] = self.default_author
            else:
                authors[post_author] = self.migrate_author(post_author)
        return authors

    def migrate_author(self, author_name):
        """Handle actions for migrating the users"""
        action_text = "The author '%s' needs to be migrated to an User:\n"\
                      "1. Use an existing user ?\n"\
                      "2. Create a new user ?\n"\
                      "Please select a choice: " % author_name
        while 42:
            selection = raw_input(smart_str(action_text))
            if selection in '12':
                break
        if selection == '1':
            users = User.objects.all()
            usernames = [user.username for user in users]
            while 42:
                user_text = "1. Select your user, by typing " \
                            "one of theses usernames:\n"\
                            "[%s]\n"\
                            "Please select a choice: " % ', '.join(usernames)
                user_selected = raw_input(user_text)
                if user_selected in usernames:
                    break
            return users.get(username=user_selected)
        else:
            create_text = "2. Please type the email of the '%s' user: " % \
                          author_name
            author_mail = raw_input(create_text)
            try:
                return User.objects.create_user(author_name, author_mail)
            except IntegrityError:
                return User.objects.get(username=author_name)

    def import_attributes(self, attribute_nodes):
        """Import all the attributes from 'wp:attribute' nodes,
        because attributes in 'item' nodes are not necessarily
        all the attributes and returning it in a dict for
        database optimizations."""
        self.write_out(self.style.STEP('- Importing attributes\n'))

        attributes = {}
        for attribute_node in attribute_nodes:
            title = attribute_node.find('{%s}cat_name' % WP_NS).text[:255]
            slug = attribute_node.find(
                '{%s}attribute_nicename' % WP_NS).text[:255]
            try:
                parent = attribute_node.find(
                    '{%s}attribute_parent' % WP_NS).text[:255]
            except TypeError:
                parent = None
            self.write_out('> %s... ' % title)
            attribute, created = Attribute.objects.get_or_create(
                title=title, slug=slug, parent=attributes.get(parent))
            attributes[title] = attribute
            self.write_out(self.style.ITEM('OK\n'))
        return attributes

    def import_tags(self, tag_nodes):
        """Import all the tags form 'wp:tag' nodes,
        because tags in 'item' nodes are not necessarily
        all the tags, then use only the nicename, because it's like
        a slug and the true tag name may be not valid for url usage."""
        self.write_out(self.style.STEP('- Importing tags\n'))
        for tag_node in tag_nodes:
            tag_name = tag_node.find(
                '{%s}tag_slug' % WP_NS).text[:50]
            self.write_out('> %s... ' % tag_name)
            Tag.objects.get_or_create(name=tag_name)
            self.write_out(self.style.ITEM('OK\n'))

    def get_attributetype_tags(self, attributes):
        """Return a list of attributetype's tags,
        by using the nicename for url compatibility"""
        tags = []
        for attribute in attributes:
            domain = attribute.attrib.get('domain', 'attribute')
            if domain == 'tag' and attribute.attrib.get('nicename'):
                tags.append(attribute.attrib.get('nicename'))
        return tags

    def get_attributetype_attributes(self, attribute_nodes):
        """Return a list of attributetype's attributes
        based of imported attributes"""
        attributes = []
        for attribute_node in attribute_nodes:
            domain = attribute_node.attrib.get('domain')
            if domain == 'attribute':
                attributes.append(self.attributes[attribute_node.text])
        return attributes

    def import_attributetype(self, title, content, item_node):
        """Importing an attributetype but some data are missing like
        the image, related attributetypes, start_publication and end_publication.
        start_publication and creation_date will use the same value,
        wich is always in Wordpress $post->post_date"""
        creation_date = datetime.strptime(
            item_node.find('{%s}post_date' % WP_NS).text, '%Y-%m-%d %H:%M:%S')

        excerpt = item_node.find('{%sexcerpt/}encoded' % WP_NS).text
        if not excerpt:
            if self.auto_excerpt:
                excerpt = truncate_words(strip_tags(content), 50)
            else:
                excerpt = ''

        attributetype_dict = {
            'content': content,
            'excerpt': excerpt,
            # Prefer use this function than
            # item_node.find('{%s}post_name' % WP_NS).text
            # Because slug can be not well formated
            'slug': slugify(title)[:255] or 'post-%s' % item_node.find(
                '{%s}post_id' % WP_NS).text,
            'tags': ', '.join(self.get_attributetype_tags(item_node.findall(
                'attribute'))),
            'status': self.REVERSE_STATUS[item_node.find(
                '{%s}status' % WP_NS).text],
            'comment_enabled': item_node.find(
                '{%s}comment_status' % WP_NS).text == 'open',
            'pingback_enabled': item_node.find(
                '{%s}ping_status' % WP_NS).text == 'open',
            'featured': item_node.find('{%s}is_sticky' % WP_NS).text == '1',
            'password': item_node.find('{%s}post_password' % WP_NS).text or '',
            'login_required': item_node.find(
                '{%s}status' % WP_NS).text == 'private',
            'creation_date': creation_date,
            'last_update': datetime.now(),
            'start_publication': creation_date}

        attributetype, created = Attributetype.objects.get_or_create(title=title,
                                                     defaults=attributetype_dict)

        attributetype.attributes.add(*self.get_attributetype_attributes(
            item_node.findall('attribute')))
        attributetype.authors.add(self.authors[item_node.find(
            '{http://purl.org/dc/elements/1.1/}creator').text])
        attributetype.sites.add(self.SITE)

        #current_id = item_node.find('{%s}post_id' % WP_NS).text
        #parent_id = item_node.find('%s}post_parent' % WP_NS).text

        return attributetype

    def import_attributetypes(self, items):
        """Loops over items and find attributetype to import,
        an attributetype need to have 'post_type' set to 'post' and
        have content."""
        self.write_out(self.style.STEP('- Importing attributetypes\n'))

        for item_node in items:
            title = (item_node.find('title').text or '')[:255]
            post_type = item_node.find('{%s}post_type' % WP_NS).text
            content = item_node.find(
                '{http://purl.org/rss/1.0/modules/content/}encoded').text

            if post_type == 'post' and content and title:
                self.write_out('> %s... ' % title)
                attributetype = self.import_attributetype(title, content, item_node)
                self.write_out(self.style.ITEM('OK\n'))
                self.import_comments(attributetype, item_node.findall(
                    '{%s}comment/' % WP_NS))
            else:
                self.write_out('> %s... ' % title, 2)
                self.write_out(self.style.NOTICE('SKIPPED (not a post)\n'), 2)

    def import_comments(self, attributetype, comment_nodes):
        """Loops over comments nodes and import then
        in django.contrib.comments"""
        for comment_node in comment_nodes:
            is_pingback = comment_node.find(
                '{%s}comment_type' % WP_NS).text == 'pingback'
            is_trackback = comment_node.find(
                '{%s}comment_type' % WP_NS).text == 'trackback'

            title = 'Comment #%s' % (comment_node.find(
                '{%s}comment_id/' % WP_NS).text)
            self.write_out(' > %s... ' % title)

            content = comment_node.find(
                '{%s}comment_content/' % WP_NS).text
            if not content:
                self.write_out(self.style.NOTICE('SKIPPED (unfilled)\n'))
                return

            submit_date = datetime.strptime(
                comment_node.find('{%s}comment_date' % WP_NS).text,
                '%Y-%m-%d %H:%M:%S')

            approvation = comment_node.find(
                '{%s}comment_approved' % WP_NS).text
            is_public = True
            is_removed = False
            if approvation != '1':
                is_removed = True
            if approvation == 'spam':
                is_public = False

            comment_dict = {
                'content_object': attributetype,
                'site': self.SITE,
                'user_name': comment_node.find(
                    '{%s}comment_author/' % WP_NS).text[:50],
                'user_email': comment_node.find(
                    '{%s}comment_author_email/' % WP_NS).text or '',
                'user_url': comment_node.find(
                    '{%s}comment_author_url/' % WP_NS).text or '',
                'comment': content,
                'submit_date': submit_date,
                'ip_address': comment_node.find(
                    '{%s}comment_author_IP/' % WP_NS).text or '',
                'is_public': is_public,
                'is_removed': is_removed, }
            comment = comments.get_model()(**comment_dict)
            comment.save()
            if approvation == 'spam':
                comment.flags.create(
                    user=attributetype.authors.all()[0], flag='spam')
            if is_pingback:
                comment.flags.create(
                    user=attributetype.authors.all()[0], flag='pingback')
            if is_trackback:
                comment.flags.create(
                    user=attributetype.authors.all()[0], flag='trackback')

            self.write_out(self.style.ITEM('OK\n'))