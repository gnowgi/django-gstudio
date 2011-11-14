"""XML-RPC methods of Objectapp metaWeblog API"""
import os
from datetime import datetime
from xmlrpclib import Fault
from xmlrpclib import DateTime

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.utils.translation import gettext as _
from django.utils.html import strip_tags
from django.utils.text import truncate_words
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.template.defaultfilters import slugify

from objectapp.models import GBObject
from objectapp.models import Objecttype
from objectapp.settings import PROTOCOL
from objectapp.settings import UPLOAD_TO
from objectapp.managers import DRAFT, PUBLISHED
from django_xmlrpc.decorators import xmlrpc_func

# http://docs.nucleuscms.org/blog/12#errorcodes
LOGIN_ERROR = 801
PERMISSION_DENIED = 803


def authenticate(username, password, permission=None):
    """Authenticate staff_user with permission"""
    try:
        user = User.objects.get(username__exact=username)
    except User.DoesNotExist:
        raise Fault(LOGIN_ERROR, _('Username is incorrect.'))
    if not user.check_password(password):
        raise Fault(LOGIN_ERROR, _('Password is invalid.'))
    if not user.is_staff or not user.is_active:
        raise Fault(PERMISSION_DENIED, _('User account unavailable.'))
    if permission:
        if not user.has_perm(permission):
            raise Fault(PERMISSION_DENIED, _('User cannot %s.') % permission)
    return user


def blog_structure(site):
    """A blog structure"""
    return {'url': '%s://%s%s' % (
        PROTOCOL, site.domain, reverse('objectapp_gbobject_archive_index')),
            'blogid': settings.SITE_ID,
            'blogName': site.name}


def user_structure(user, site):
    """An user structure"""
    return {'userid': user.pk,
            'email': user.email,
            'nickname': user.username,
            'lastname': user.last_name,
            'firstname': user.first_name,
            'url': '%s://%s%s' % (
                PROTOCOL, site.domain,
                reverse('objectapp_author_detail', args=[user.username]))}


def author_structure(user):
    """An author structure"""
    return {'user_id': user.pk,
            'user_login': user.username,
            'display_name': user.username,
            'user_email': user.email}


def objecttype_structure(objecttype, site):
    """A objecttype structure"""
    return {'description': objecttype.title,
            'htmlUrl': '%s://%s%s' % (
                PROTOCOL, site.domain,
                objecttype.get_absolute_url()),
            'rssUrl': '%s://%s%s' % (
                PROTOCOL, site.domain,
                reverse('objectapp_objecttype_feed', args=[objecttype.tree_path])),
            # Useful Wordpress Extensions
            'objecttypeId': objecttype.pk,
            'parentId': objecttype.parent and objecttype.parent.pk or 0,
            'objecttypeDescription': objecttype.description,
            'objecttypeName': objecttype.title}


def post_structure(gbobject, site):
    """A post structure with extensions"""
    author = gbobject.authors.all()[0]
    return {'title': gbobject.title,
            'description': unicode(gbobject.html_content),
            'link': '%s://%s%s' % (PROTOCOL, site.domain,
                                   gbobject.get_absolute_url()),
            # Basic Extensions
            'permaLink': '%s://%s%s' % (PROTOCOL, site.domain,
                                        gbobject.get_absolute_url()),
            'objecttypes': [cat.title for cat in gbobject.objecttypes.all()],
            'dateCreated': DateTime(gbobject.creation_date.isoformat()),
            'postid': gbobject.pk,
            'userid': author.username,
            # Useful Movable Type Extensions
            'mt_excerpt': gbobject.excerpt,
            'mt_allow_comments': int(gbobject.comment_enabled),
            'mt_allow_pings': int(gbobject.pingback_enabled),
            'mt_keywords': gbobject.tags,
            # Useful Wordpress Extensions
            'wp_author': author.username,
            'wp_author_id': author.pk,
            'wp_author_display_name': author.username,
            'wp_password': gbobject.password,
            'wp_slug': gbobject.slug,
            'sticky': gbobject.featured}


@xmlrpc_func(returns='struct[]', args=['string', 'string', 'string'])
def get_users_blogs(apikey, username, password):
    """blogger.getUsersBlogs(api_key, username, password)
    => blog structure[]"""
    authenticate(username, password)
    site = Site.objects.get_current()
    return [blog_structure(site)]


@xmlrpc_func(returns='struct', args=['string', 'string', 'string'])
def get_user_info(apikey, username, password):
    """blogger.getUserInfo(api_key, username, password)
    => user structure"""
    user = authenticate(username, password)
    site = Site.objects.get_current()
    return user_structure(user, site)


@xmlrpc_func(returns='struct[]', args=['string', 'string', 'string'])
def get_authors(apikey, username, password):
    """wp.getAuthors(api_key, username, password)
    => author structure[]"""
    authenticate(username, password)
    return [author_structure(author)
            for author in User.objects.filter(is_staff=True)]


@xmlrpc_func(returns='boolean', args=['string', 'string',
                                      'string', 'string', 'string'])
def delete_post(apikey, post_id, username, password, publish):
    """blogger.deletePost(api_key, post_id, username, password, 'publish')
    => boolean"""
    user = authenticate(username, password, 'objectapp.delete_gbobject')
    gbobject = GBObject.objects.get(id=post_id, authors=user)
    gbobject.delete()
    return True


@xmlrpc_func(returns='struct', args=['string', 'string', 'string'])
def get_post(post_id, username, password):
    """metaWeblog.getPost(post_id, username, password)
    => post structure"""
    user = authenticate(username, password)
    site = Site.objects.get_current()
    return post_structure(GBObject.objects.get(id=post_id, authors=user), site)


@xmlrpc_func(returns='struct[]',
             args=['string', 'string', 'string', 'integer'])
def get_recent_posts(blog_id, username, password, number):
    """metaWeblog.getRecentPosts(blog_id, username, password, number)
    => post structure[]"""
    user = authenticate(username, password)
    site = Site.objects.get_current()
    return [post_structure(gbobject, site) \
            for gbobject in GBObject.objects.filter(authors=user)[:number]]


@xmlrpc_func(returns='struct[]', args=['string', 'string', 'string'])
def get_objecttypes(blog_id, username, password):
    """metaWeblog.getObjecttypes(blog_id, username, password)
    => objecttype structure[]"""
    authenticate(username, password)
    site = Site.objects.get_current()
    return [objecttype_structure(objecttype, site) \
            for objecttype in Objecttype.objects.all()]


@xmlrpc_func(returns='string', args=['string', 'string', 'string', 'struct'])
def new_objecttype(blog_id, username, password, objecttype_struct):
    """wp.newObjecttype(blog_id, username, password, objecttype)
    => objecttype_id"""
    authenticate(username, password, 'objectapp.add_objecttype')
    objecttype_dict = {'title': objecttype_struct['name'],
                     'description': objecttype_struct['description'],
                     'slug': objecttype_struct['slug']}
    if int(objecttype_struct['parent_id']):
        objecttype_dict['parent'] = Objecttype.objects.get(
            pk=objecttype_struct['parent_id'])
    objecttype = Objecttype.objects.create(**objecttype_dict)

    return objecttype.pk


@xmlrpc_func(returns='string', args=['string', 'string', 'string',
                                     'struct', 'boolean'])
def new_post(blog_id, username, password, post, publish):
    """metaWeblog.newPost(blog_id, username, password, post, publish)
    => post_id"""
    user = authenticate(username, password, 'objectapp.add_gbobject')
    if post.get('dateCreated'):
        creation_date = datetime.strptime(
            post['dateCreated'].value.replace('Z', '').replace('-', ''),
            '%Y%m%dT%H:%M:%S')
    else:
        creation_date = datetime.now()

    gbobject_dict = {'title': post['title'],
                  'content': post['description'],
                  'excerpt': post.get('mt_excerpt', truncate_words(
                      strip_tags(post['description']), 50)),
                  'creation_date': creation_date,
                  'last_update': creation_date,
                  'comment_enabled': post.get('mt_allow_comments', 1) == 1,
                  'pingback_enabled': post.get('mt_allow_pings', 1) == 1,
                  'featured': post.get('sticky', 0) == 1,
                  'tags': 'mt_keywords' in post and post['mt_keywords'] or '',
                  'slug': 'wp_slug' in post and post['wp_slug'] or slugify(
                      post['title']),
                  'password': post.get('wp_password', ''),
                  'status': publish and PUBLISHED or DRAFT}
    gbobject = GBObject.objects.create(**gbobject_dict)

    author = user
    if 'wp_author_id' in post and user.has_perm('objectapp.can_change_author'):
        if int(post['wp_author_id']) != user.pk:
            author = User.objects.get(pk=post['wp_author_id'])
    gbobject.authors.add(author)

    gbobject.sites.add(Site.objects.get_current())
    if 'objecttypes' in post:
        gbobject.objecttypes.add(*[Objecttype.objects.get_or_create(
            title=cat, slug=slugify(cat))[0]
                               for cat in post['objecttypes']])

    return gbobject.pk


@xmlrpc_func(returns='boolean', args=['string', 'string', 'string',
                                      'struct', 'boolean'])
def edit_post(post_id, username, password, post, publish):
    """metaWeblog.editPost(post_id, username, password, post, publish)
    => boolean"""
    user = authenticate(username, password, 'objectapp.change_gbobject')
    gbobject = GBObject.objects.get(id=post_id, authors=user)
    if post.get('dateCreated'):
        creation_date = datetime.strptime(
            post['dateCreated'].value.replace('Z', '').replace('-', ''),
            '%Y%m%dT%H:%M:%S')
    else:
        creation_date = gbobject.creation_date

    gbobject.title = post['title']
    gbobject.content = post['description']
    gbobject.excerpt = post.get('mt_excerpt', truncate_words(
        strip_tags(post['description']), 50))
    gbobject.creation_date = creation_date
    gbobject.last_update = datetime.now()
    gbobject.comment_enabled = post.get('mt_allow_comments', 1) == 1
    gbobject.pingback_enabled = post.get('mt_allow_pings', 1) == 1
    gbobject.featured = post.get('sticky', 0) == 1
    gbobject.tags = 'mt_keywords' in post and post['mt_keywords'] or ''
    gbobject.slug = 'wp_slug' in post and post['wp_slug'] or slugify(
        post['title'])
    gbobject.status = publish and PUBLISHED or DRAFT
    gbobject.password = post.get('wp_password', '')
    gbobject.save()

    if 'wp_author_id' in post and user.has_perm('objectapp.can_change_author'):
        if int(post['wp_author_id']) != user.pk:
            author = User.objects.get(pk=post['wp_author_id'])
            gbobject.authors.clear()
            gbobject.authors.add(author)

    if 'objecttypes' in post:
        gbobject.objecttypes.clear()
        gbobject.objecttypes.add(*[Objecttype.objects.get_or_create(
            title=cat, slug=slugify(cat))[0]
                               for cat in post['objecttypes']])
    return True


@xmlrpc_func(returns='struct', args=['string', 'string', 'string', 'struct'])
def new_media_object(blog_id, username, password, media):
    """metaWeblog.newMediaObject(blog_id, username, password, media)
    => media structure"""
    authenticate(username, password)
    path = default_storage.save(os.path.join(UPLOAD_TO, media['name']),
                                ContentFile(media['bits'].data))
    return {'url': default_storage.url(path)}
