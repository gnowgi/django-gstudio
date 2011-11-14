"""Test cases for Attributeapp's moderator"""
from django.core import mail
from django.test import TestCase
from django.contrib import comments
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.contrib.contenttypes.models import ContentType

from attributeapp.models import Attributetype
from attributeapp.managers import PUBLISHED
from attributeapp.moderator import AttributetypeCommentModerator


class AttributetypeCommentModeratorTestCase(TestCase):
    """Test cases for the moderator"""

    def setUp(self):
        self.site = Site.objects.get_current()
        self.author = User.objects.create(username='admin',
                                          email='admin@example.com')
        self.attributetype_ct_id = ContentType.objects.get_for_model(Attributetype).pk

        params = {'title': 'My test attributetype',
                  'content': 'My test attributetype',
                  'slug': 'my-test-attributetype',
                  'status': PUBLISHED}
        self.attributetype = Attributetype.objects.create(**params)
        self.attributetype.sites.add(self.site)
        self.attributetype.authors.add(self.author)

    def test_email(self):
        comment = comments.get_model().objects.create(
            comment='My Comment', user=self.author, is_public=True,
            content_object=self.attributetype, site=self.site)
        self.assertEquals(len(mail.outbox), 0)
        moderator = AttributetypeCommentModerator(Attributetype)
        moderator.email_reply = False
        moderator.email_authors = False
        moderator.mail_comment_notification_recipients = []
        moderator.email(comment, self.attributetype, 'request')
        self.assertEquals(len(mail.outbox), 0)
        moderator.email_reply = True
        moderator.email_authors = True
        moderator.mail_comment_notification_recipients = ['admin@example.com']
        moderator.email(comment, self.attributetype, 'request')
        self.assertEquals(len(mail.outbox), 1)

    def test_do_email_notification(self):
        comment = comments.get_model().objects.create(
            comment='My Comment', user=self.author, is_public=True,
            content_object=self.attributetype, site=self.site)
        self.assertEquals(len(mail.outbox), 0)
        moderator = AttributetypeCommentModerator(Attributetype)
        moderator.mail_comment_notification_recipients = ['admin@example.com']
        moderator.do_email_notification(comment, self.attributetype, 'request')
        self.assertEquals(len(mail.outbox), 1)

    def test_do_email_authors(self):
        comment = comments.get_model().objects.create(
            comment='My Comment', user=self.author, is_public=True,
            content_object=self.attributetype, site=self.site)
        self.assertEquals(len(mail.outbox), 0)
        moderator = AttributetypeCommentModerator(Attributetype)
        moderator.email_authors = True
        moderator.mail_comment_notification_recipients = ['admin@example.com']
        moderator.do_email_authors(comment, self.attributetype, 'request')
        self.assertEquals(len(mail.outbox), 0)
        moderator.mail_comment_notification_recipients = []
        moderator.do_email_authors(comment, self.attributetype, 'request')
        self.assertEquals(len(mail.outbox), 1)

    def test_do_email_reply(self):
        comment = comments.get_model().objects.create(
            comment='My Comment 1', user=self.author, is_public=True,
            content_object=self.attributetype, site=self.site)
        moderator = AttributetypeCommentModerator(Attributetype)
        moderator.email_notification_reply = True
        moderator.mail_comment_notification_recipients = ['admin@example.com']
        moderator.do_email_reply(comment, self.attributetype, 'request')
        self.assertEquals(len(mail.outbox), 0)

        comment = comments.get_model().objects.create(
            comment='My Comment 2', user_email='user_1@example.com',
            content_object=self.attributetype, is_public=True, site=self.site)
        moderator.do_email_reply(comment, self.attributetype, 'request')
        self.assertEquals(len(mail.outbox), 0)

        comment = comments.get_model().objects.create(
            comment='My Comment 3', user_email='user_2@example.com',
            content_object=self.attributetype, is_public=True, site=self.site)
        moderator.do_email_reply(comment, self.attributetype, 'request')
        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(mail.outbox[0].bcc, [u'user_1@example.com'])

        comment = comments.get_model().objects.create(
            comment='My Comment 4', user=self.author, is_public=True,
            content_object=self.attributetype, site=self.site)
        moderator.do_email_reply(comment, self.attributetype, 'request')
        self.assertEquals(len(mail.outbox), 2)
        self.assertEquals(mail.outbox[1].bcc, [u'user_1@example.com',
                                               u'user_2@example.com'])

    def test_moderate(self):
        comment = comments.get_model().objects.create(
            comment='My Comment', user=self.author, is_public=True,
            content_object=self.attributetype, site=self.site)
        moderator = AttributetypeCommentModerator(Attributetype)
        moderator.auto_moderate_comments = True
        moderator.spam_checker_backends = ()
        self.assertEquals(moderator.moderate(comment, self.attributetype, 'request'),
                          True)
        moderator.auto_moderate_comments = False
        self.assertEquals(moderator.moderate(comment, self.attributetype, 'request'),
                          False)
        self.assertEquals(comments.get_model().objects.filter(
            flags__flag='spam').count(), 0)
        moderator.spam_checker_backends = (
            'attributeapp.spam_checker.backends.all_is_spam',)
        self.assertEquals(moderator.moderate(comment, self.attributetype, 'request'),
                          True)
        self.assertEquals(comments.get_model().objects.filter(
            flags__flag='spam').count(), 1)
