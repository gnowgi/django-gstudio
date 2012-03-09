"""
This file was generated with the customdashboard management command and
contains the class for the main dashboard.

To activate your index dashboard add the following to your settings.py::
    GRAPPELLI_INDEX_DASHBOARD = 'demo.dashboard.CustomIndexDashboard'
"""

from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse

from grappelli.dashboard import modules, Dashboard
from grappelli.dashboard.utils import get_admin_site_name


class CustomIndexDashboard(Dashboard):
    """
    Custom index dashboard for atlas.gnowledge.org
    """
    
    def init_with_context(self, context):
        site_name = get_admin_site_name(context)
        
        # append a group for "Administration" & "Applications"
        self.children.append(modules.Group(
            _('Group: Administration & Applications'),
            column=1,
            collapsible=False,
            children = [
                modules.AppList(
                        #Gstudio models here ( other than attribute datatype)
                        _('Gstudio'),
                        column=1,
                        collapsible=False,
                        models=(
                            'gstudio.models.Objecttype',
                            'gstudio.models.Metatype',
                            'gstudio.models.Relation',
                            'gstudio.models.Relationtype',
                            'gstudio.models.Attribute',
                            'gstudio.models.Attributetype',
                            'gstudio.models.Systemtype',
                            'gstudio.models.Processtype',
                            'gstudio.models.AttributeSpecification',
                            'gstudio.models.RelationSpecification',
                            'gstudio.models.NodeSpecification',
                            'gstudio.models.Union',
                            'gstudio.models.Complement',
                            'gstudio.models.Intersection',
                            'gstudio.models.Expression',
                            ),

                        ),
                #Object App models here

                modules.AppList(
                        _('Object App'),
                        column=1,
                        collapsible=False,
                        models=(
                            'objectapp.models.*',
                            ),
                        ),



                # Gstudio Attribute datatype models here

                modules.AppList(
                        _('Attribute Manager'),
                        column=1,
                        collapsible=True,
                        models=(
                            'gstudio.models.AttributeCharField',
                            'gstudio.models.AttributeTextField',
                            'gstudio.models.AttributeIntegerField',
                            'gstudio.models.AttributeCommaSeparatedIntegerField',
                            'gstudio.models.AttributeBigIntegerField',
                            'gstudio.models.AttributePositiveIntegerField',
                            'gstudio.models.AttributeDecimalField',
                            'gstudio.models.AttributeFloatField',
                            'gstudio.models.AttributeBooleanField',
                            'gstudio.models.AttributeNullBooleanField',
                            'gstudio.models.AttributeDateField',
                            'gstudio.models.AttributeDateTimeField',
                            'gstudio.models.AttributeTimeField',
                            'gstudio.models.AttributeEmailField',
                            'gstudio.models.AttributeFileField',
                            'gstudio.models.AttributeFilePathField',
                            'gstudio.models.AttributeImageField',
                            'gstudio.models.AttributeURLField',

                            ),
                        ),


                modules.AppList(
                    _('Other Applications'),
                    column=1,
#                    css_classes=('collapse closed',),
                    exclude=('django.contrib.*','gstudio.models.*','objectapp.models.*'),),
                modules.AppList(
                        _('Administration'),
                        column=1,
                        collapsible=False,
                        models=('django.contrib.*',),
                        ),




                
                        ]
                ))
        


        # append an app list module for "Applications"
        self.children.append(modules.AppList(
            _('AppList: Applications'),
            collapsible=False,
            column=2,
            css_classes=('collapse closed',),
            exclude=('django.contrib.*',),
        ))

        
        # append an app list module for "Administration"
        self.children.append(modules.ModelList(
            _('ModelList: Administration'),
            column=2,
            collapsible=False,
            models=('django.contrib.*',),
            children=[
                {
                    'title': _('FileBrowser'),
                    'url': '/admin/filebrowser/browse/',
                    'external': False,
                },
            ]

        ))
        
        # append another link list module for "support".
        self.children.append(modules.LinkList(
            _('Media Management'),
            column=2,
            children=[
                {
                    'title': _('FileBrowser'),
                    'url': '/admin/filebrowser/browse/',
                    'external': False,
                },
            ]
        ))
        
        # append another link list module for "support".
        self.children.append(modules.LinkList(
            _('Support'),
            column=2,
            children=[
                {
                    'title': _('Django Documentation'),
                    'url': 'http://docs.djangoproject.com/',
                    'external': True,
                },
                {
                    'title': _('Grappelli Documentation'),
                    'url': 'http://packages.python.org/django-grappelli/',
                    'external': True,
                },
                {
                    'title': _('Grappelli Google-Code'),
                    'url': 'http://code.google.com/p/django-grappelli/',
                    'external': True,
                },
            ]
        ))
        
        # append a feed module
        self.children.append(modules.Feed(
            _('Latest Django News'),
            column=2,
            feed_url='http://www.djangoproject.com/rss/weblog/',
            limit=5
        ))
        
        # append a recent actions module
        self.children.append(modules.RecentActions(
            _('Recent Actions'),
            limit=5,
            collapsible=False,
            column=3,
        ))


