"""Test cases for Relationapp's Relationtype"""
from __future__ import with_statement
import warnings
from datetime import datetime
from datetime import timedelta

from django.test import TestCase
from django.conf import settings
from django.contrib import comments
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.contrib.comments.models import CommentFlag

from relationapp import models
from relationapp.models import Relationtype
from relationapp.managers import PUBLISHED
from relationapp.models import get_base_model
from relationapp.models import Relationtype
from relationapp import models as models_settings
from relationapp import url_shortener as shortener_settings


class RelationtypeTestCase(TestCase):

    def setUp(self):
        params = {'title': 'My relationtype',
                  'content': 'My content',
                  'slug': 'my-relationtype'}
        self.relationtype = Relationtype.objects.create(**params)

    def test_discussions(self):
        site = Site.objects.get_current()
        self.assertEquals(self.relationtype.discussions.count(), 0)
        self.assertEquals(self.relationtype.comments.count(), 0)
        self.assertEquals(self.relationtype.pingbacks.count(), 0)
        self.assertEquals(self.relationtype.trackbacks.count(), 0)

        comments.get_model().objects.create(comment='My Comment 1',
                                            content_object=self.relationtype,
                                            site=site)
        self.assertEquals(self.relationtype.discussions.count(), 1)
        self.assertEquals(self.relationtype.comments.count(), 1)
        self.assertEquals(self.relationtype.pingbacks.count(), 0)
        self.assertEquals(self.relationtype.trackbacks.count(), 0)

        comments.get_model().objects.create(comment='My Comment 2',
                                            content_object=self.relationtype,
                                            site=site, is_public=False)
        self.assertEquals(self.relationtype.discussions.count(), 1)
        self.assertEquals(self.relationtype.comments.count(), 1)
        self.assertEquals(self.relationtype.pingbacks.count(), 0)
        self.assertEquals(self.relationtype.trackbacks.count(), 0)

        author = User.objects.create_user(username='webmaster',
                                          email='webmaster@example.com')

        comment = comments.get_model().objects.create(
            comment='My Comment 3',
            content_object=self.relationtype,
            site=Site.objects.create(domain='http://toto.com',
                                     name='Toto.com'))
        comment.flags.create(user=author, flag=CommentFlag.MODERATOR_APPROVAL)
        self.assertEquals(self.relationtype.discussions.count(), 2)
        self.assertEquals(self.relationtype.comments.count(), 2)
        self.assertEquals(self.relationtype.pingbacks.count(), 0)
        self.assertEquals(self.relationtype.trackbacks.count(), 0)

        comment = comments.get_model().objects.create(
            comment='My Pingback 1', content_object=self.relationtype, site=site)
        comment.flags.create(user=author, flag='pingback')
        self.assertEquals(self.relationtype.discussions.count(), 3)
        self.assertEquals(self.relationtype.comments.count(), 2)
        self.assertEquals(self.relationtype.pingbacks.count(), 1)
        self.assertEquals(self.relationtype.trackbacks.count(), 0)

        comment = comments.get_model().objects.create(
            comment='My Trackback 1', content_object=self.relationtype, site=site)
        comment.flags.create(user=author, flag='trackback')
        self.assertEquals(self.relationtype.discussions.count(), 4)
        self.assertEquals(self.relationtype.comments.count(), 2)
        self.assertEquals(self.relationtype.pingbacks.count(), 1)
        self.assertEquals(self.relationtype.trackbacks.count(), 1)

    def test_str(self):
        self.assertEquals(str(self.relationtype), 'My relationtype: draft')

    def test_word_count(self):
        self.assertEquals(self.relationtype.word_count, 2)

    def test_comments_are_open(self):
        original_auto_close = models.AUTO_CLOSE_COMMENTS_AFTER
        models.AUTO_CLOSE_COMMENTS_AFTER = None
        self.assertEquals(self.relationtype.comments_are_open, True)
        models.AUTO_CLOSE_COMMENTS_AFTER = 5
        self.relationtype.start_publication = datetime.now() - timedelta(days=7)
        self.relationtype.save()
        self.assertEquals(self.relationtype.comments_are_open, False)

        models.AUTO_CLOSE_COMMENTS_AFTER = original_auto_close

    def test_is_actual(self):
        self.assertTrue(self.relationtype.is_actual)
        self.relationtype.start_publication = datetime(2020, 3, 15)
        self.assertFalse(self.relationtype.is_actual)
        self.relationtype.start_publication = datetime.now()
        self.assertTrue(self.relationtype.is_actual)
        self.relationtype.end_publication = datetime(2000, 3, 15)
        self.assertFalse(self.relationtype.is_actual)

    def test_is_visible(self):
        self.assertFalse(self.relationtype.is_visible)
        self.relationtype.status = PUBLISHED
        self.assertTrue(self.relationtype.is_visible)
        self.relationtype.start_publication = datetime(2020, 3, 15)
        self.assertFalse(self.relationtype.is_visible)

    def test_short_url(self):
        original_shortener = shortener_settings.URL_SHORTENER_BACKEND
        shortener_settings.URL_SHORTENER_BACKEND = 'relationapp.url_shortener.'\
                                                   'backends.default'
        self.assertEquals(self.relationtype.short_url,
                          'http://example.com' +
                          reverse('relationapp_relationtype_shortlink',
                                  args=[self.relationtype.pk]))
        shortener_settings.URL_SHORTENER_BACKEND = original_shortener

    def test_previous_relationtype(self):
        site = Site.objects.get_current()
        self.assertFalse(self.relationtype.previous_relationtype)
        params = {'title': 'My second relationtype',
                  'content': 'My second content',
                  'slug': 'my-second-relationtype',
                  'creation_date': datetime(2000, 1, 1),
                  'status': PUBLISHED}
        self.second_relationtype = Relationtype.objects.create(**params)
        self.second_relationtype.sites.add(site)
        self.assertEquals(self.relationtype.previous_relationtype, self.second_relationtype)
        params = {'title': 'My third relationtype',
                  'content': 'My third content',
                  'slug': 'my-third-relationtype',
                  'creation_date': datetime(2001, 1, 1),
                  'status': PUBLISHED}
        self.third_relationtype = Relationtype.objects.create(**params)
        self.third_relationtype.sites.add(site)
        self.assertEquals(self.relationtype.previous_relationtype, self.third_relationtype)
        self.assertEquals(self.third_relationtype.previous_relationtype, self.second_relationtype)

    def test_next_relationtype(self):
        site = Site.objects.get_current()
        self.assertFalse(self.relationtype.next_relationtype)
        params = {'title': 'My second relationtype',
                  'content': 'My second content',
                  'slug': 'my-second-relationtype',
                  'creation_date': datetime(2100, 1, 1),
                  'status': PUBLISHED}
        self.second_relationtype = Relationtype.objects.create(**params)
        self.second_relationtype.sites.add(site)
        self.assertEquals(self.relationtype.next_relationtype, self.second_relationtype)
        params = {'title': 'My third relationtype',
                  'content': 'My third content',
                  'slug': 'my-third-relationtype',
                  'creation_date': datetime(2050, 1, 1),
                  'status': PUBLISHED}
        self.third_relationtype = Relationtype.objects.create(**params)
        self.third_relationtype.sites.add(site)
        self.assertEquals(self.relationtype.next_relationtype, self.third_relationtype)
        self.assertEquals(self.third_relationtype.next_relationtype, self.second_relationtype)

    def test_related_published(self):
        site = Site.objects.get_current()
        self.assertFalse(self.relationtype.related_published)
        params = {'title': 'My second relationtype',
                  'content': 'My second content',
                  'slug': 'my-second-relationtype',
                  'status': PUBLISHED}
        self.second_relationtype = Relationtype.objects.create(**params)
        self.second_relationtype.related.add(self.relationtype)
        self.assertEquals(len(self.relationtype.related_published), 0)

        self.second_relationtype.sites.add(site)
        self.assertEquals(len(self.relationtype.related_published), 1)
        self.assertEquals(len(self.second_relationtype.related_published), 0)

        self.relationtype.status = PUBLISHED
        self.relationtype.save()
        self.relationtype.sites.add(site)
        self.assertEquals(len(self.relationtype.related_published), 1)
        self.assertEquals(len(self.second_relationtype.related_published), 1)


class RelationtypeHtmlContentTestCase(TestCase):

    def setUp(self):
        params = {'title': 'My relationtype',
                  'content': 'My content',
                  'slug': 'my-relationtype'}
        self.relationtype = Relationtype(**params)
        self.original_debug = settings.DEBUG
        self.original_rendering = models_settings.MARKUP_LANGUAGE
        settings.DEBUG = False

    def tearDown(self):
        settings.DEBUG = self.original_debug
        models_settings.MARKUP_LANGUAGE = self.original_rendering

    def test_html_content_default(self):
        models_settings.MARKUP_LANGUAGE = None
        self.assertEquals(self.relationtype.html_content, '<p>My content</p>')

        self.relationtype.content = 'Hello world !\n' \
                             ' this is my content'
        self.assertEquals(self.relationtype.html_content,
                          '<p>Hello world !<br /> this is my content</p>')

    def test_html_content_textitle(self):
        models_settings.MARKUP_LANGUAGE = 'textile'
        self.relationtype.content = 'Hello world !\n\n' \
                             'this is my content :\n\n' \
                             '* Item 1\n* Item 2'
        html_content = self.relationtype.html_content
        try:
            self.assertEquals(html_content,
                              '\t<p>Hello world !</p>\n\n\t' \
                              '<p>this is my content :</p>\n\n\t' \
                              '<ul>\n\t\t<li>Item 1</li>\n\t\t' \
                              '<li>Item 2</li>\n\t</ul>')
        except AssertionError:
            self.assertEquals(html_content, self.relationtype.content)

    def test_html_content_markdown(self):
        models_settings.MARKUP_LANGUAGE = 'markdown'
        self.relationtype.content = 'Hello world !\n\n' \
                             'this is my content :\n\n' \
                             '* Item 1\n* Item 2'
        html_content = self.relationtype.html_content
        try:
            self.assertEquals(html_content,
                              '<p>Hello world !</p>\n' \
                              '<p>this is my content :</p>'\
                              '\n<ul>\n<li>Item 1</li>\n' \
                              '<li>Item 2</li>\n</ul>')
        except AssertionError:
            self.assertEquals(html_content, self.relationtype.content)

    def test_html_content_restructuredtext(self):
        models_settings.MARKUP_LANGUAGE = 'restructuredtext'
        self.relationtype.content = 'Hello world !\n\n' \
                             'this is my content :\n\n' \
                             '* Item 1\n* Item 2'
        html_content = self.relationtype.html_content
        try:
            self.assertEquals(html_content,
                              '<p>Hello world !</p>\n' \
                              '<p>this is my content :</p>'\
                              '\n<ul class="simple">\n<li>Item 1</li>\n' \
                              '<li>Item 2</li>\n</ul>\n')
        except AssertionError:
            self.assertEquals(html_content, self.relationtype.content)

# this class can be removed since the base abstract class is no longer present.
class RelationtypeGetBaseModelTestCase(TestCase):

    def setUp(self):
        self.original_relationtype_base_model = models_settings.RELATIONTYPE_BASE_MODEL

    def tearDown(self):
        models_settings.RELATIONTYPE_BASE_MODEL = self.original_relationtype_base_model

    def test_get_base_model(self):
        models_settings.RELATIONTYPE_BASE_MODEL = ''
        self.assertEquals(get_base_model(), Relationtype)

        models_settings.RELATIONTYPE_BASE_MODEL = 'mymodule.myclass'
        try:
            with warnings.catch_warnings(record=True) as w:
                self.assertEquals(get_base_model(), Relationtype)
                self.assertTrue(issubclass(w[-1].relation, RuntimeWarning))
        except AttributeError:
            # Fail under Python2.5, because of'warnings.catch_warnings'
            pass

        models_settings.RELATIONTYPE_BASE_MODEL = 'relationapp.models.Relationtype'
        self.assertEquals(get_base_model(), Relationtype)