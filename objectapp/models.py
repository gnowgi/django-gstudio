"""Models of Objectapp"""
import warnings
from datetime import datetime

from django.db import models
from django.db.models import Q
from django.utils.html import strip_tags
from django.utils.html import linebreaks
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.db.models.signals import post_save
from django.utils.importlib import import_module
from django.contrib import comments
from django.contrib.comments.models import CommentFlag
from django.contrib.comments.moderation import moderator
from django.utils.translation import ugettext_lazy as _
import json
from django.contrib.markup.templatetags.markup import markdown
from django.contrib.markup.templatetags.markup import textile
from django.contrib.markup.templatetags.markup import restructuredtext


from djangoratings.fields import RatingField
from tagging.fields import TagField
from gstudio.models import Nodetype
from gstudio.models import Objecttype
from gstudio.models import Relationtype
from gstudio.models import Systemtype
from gstudio.models import Processtype
from gstudio.models import Attributetype
from gstudio.models import Attribute
from gstudio.models import Relation
from gstudio.models import Node
from gstudio.models import Edge
from gstudio.models import Author

import reversion
from objectapp.settings import UPLOAD_TO
from objectapp.settings import MARKUP_LANGUAGE
from objectapp.settings import GBOBJECT_TEMPLATES
from objectapp.settings import GBOBJECT_BASE_MODEL
from objectapp.settings import MARKDOWN_EXTENSIONS
from objectapp.settings import AUTO_CLOSE_COMMENTS_AFTER
from objectapp.managers import gbobjects_published
from objectapp.managers import GbobjectPublishedManager
from objectapp.managers import AuthorPublishedManager
from objectapp.managers import DRAFT, HIDDEN, PUBLISHED
from objectapp.moderator import GbobjectCommentModerator
from objectapp.url_shortener import get_url_shortener
from objectapp.signals import ping_directories_handler
from objectapp.signals import ping_external_urls_handler

'''
class Author(User):
    """Proxy Model around User"""

    objects = models.Manager()
    published = AuthorPublishedManager()

    def gbobjects_published(self):
        """Return only the gbobjects published"""
        return gbobjects_published(self.gbobjects)

    #@models.permalink
    def get_absolute_url(self):
        """Return author's URL"""
        return "/authors/%s/" %(self.username)
        #return ('objectapp_author_detail', (self.username,))

    class Meta:
        """Author's Meta"""
        proxy = True
'''


class Gbobject(Node):
    """
    Member nodes of object types. This is actually to be named the
    Object class, since 'Object' is a reserved name in Python, we
    prefix this with 'Gb', to suggest that it is an object of the gnowledge
    base.  System and Process classes also inherit this class.
    """


    STATUS_CHOICES = ((DRAFT, _('draft')),
                      (HIDDEN, _('hidden')),
                      (PUBLISHED, _('published')))

    content = models.TextField(_('content'), null=True, blank=True)
    image = models.ImageField(_('image'), upload_to=UPLOAD_TO,
                              blank=True, help_text=_('used for illustration'))

    excerpt = models.TextField(_('excerpt'), blank=True,
                                help_text=_('optional element'))

    prior_nodes = models.ManyToManyField('self', null=True, blank=True,
                               verbose_name=_('depends on'),
                               related_name='posterior_nodes')

    posterior_nodes = models.ManyToManyField('self', null=True, blank=True,
                               verbose_name=_('required for'),
                               related_name='prior_nodes')


    tags = TagField(_('tags'))
    objecttypes = models.ManyToManyField(Nodetype, verbose_name=_('member of'),
                                        related_name='member_objects',
                                        blank=True, null=True)
  

    authors = models.ManyToManyField(User, verbose_name=_('authors'),
                                     related_name='gbobjects',
                                     blank=True, null=False)
    status = models.IntegerField(choices=STATUS_CHOICES, default=PUBLISHED)

    featured = models.BooleanField(_('featured'), default=False)
    comment_enabled = models.BooleanField(_('comment enabled'), default=True)
    pingback_enabled = models.BooleanField(_('linkback enabled'), default=True)

        
    start_publication = models.DateTimeField(_('start publication'),
                                             help_text=_('date start publish'),
                                             default=datetime.now)
    end_publication = models.DateTimeField(_('end publication'),
                                           help_text=_('date end publish'),
                                           default=datetime(2042, 3, 15))

    sites = models.ManyToManyField(Site, verbose_name=_('sites publication'),
                                   related_name='gbobjects')

    login_required = models.BooleanField(
        _('login required'), default=False,
        help_text=_('only authenticated users can view the gbobject'))
    password = models.CharField(
        _('password'), max_length=50, blank=True,
        help_text=_('protect the gbobject with a password'))

    template = models.CharField(
        _('template'), max_length=250,
        default='objectapp/gbobject_detail.html',
        choices=[('objectapp/gbobject_detail.html', _('Default template'))] + \
        GBOBJECT_TEMPLATES,
        help_text=_('template used to display the gbobject'))

    objects = models.Manager()
    published = GbobjectPublishedManager()


    def get_relations(self):
        relation_set = {}
        # ALGO to find the relations and their left-subjecttypes and right_subjecttypes
        # 1. Get the relations containing a reference to the object. Retrieve where it occurs (left or right)
        # 2. Find out which RT they come from.
        # 3. For each RT, create a dict key and a value as a dict. And add the relation as a new key-value pair (rid:subject).
        # 4. If self is in right value, then add inverse relation as RT and add the relation as a new key-value pair (rid:subject).

        left_relset = Relation.objects.filter(left_subject=self.id) 
        right_relset = Relation.objects.filter(right_subject=self.id) 
        
        #return left_relset + right_relset

        # RT dictionary to store a single relation
        rel_dict ={}
        rel_dict['left-subjecttypes'] = {}
        rel_dict['right_subjecttypes'] ={}

               
        for relation in left_relset:
            # check if relation already exists
            if relation.relationtype.title not in rel_dict['left-subjecttypes'].keys():
                # create a new list field and add to it
                rel_dict['left-subjecttypes'][str(relation.relationtype.title)] = []
            # add 
            rel_dict['left-subjecttypes'][str(relation.relationtype.title)].append(relation) 

        for relation in right_relset:
            # check if relation exists
            if relation.relationtype.inverse not in rel_dict['right_subjecttypes'].keys():
                # create a new list key field and add to it
                rel_dict['right_subjecttypes'][str(relation.relationtype.inverse)] = []
                # add to the existing key
            rel_dict['right_subjecttypes'][str(relation.relationtype.inverse)].append(relation)

        relation_set.update(rel_dict['left-subjecttypes'])
        relation_set.update(rel_dict['right_subjecttypes'])
        
        return relation_set
        

    def get_attributes(self):
        attributes =  {}
        for attribute in Attribute.objects.filter(subject=self.id):
            for key,value in attribute.edge_node_dict.iteritems():
                attributes[key]= value
                
        return attributes
            
    
    
    def get_possible_rels(self):
        """
        Gets the relations possible for this metatype
        1. Recursively create a set of all the ancestors i.e. parent/subtypes of the MT. 
        2. Get all the R's linked to each ancestor 
        """
        #Step 1. 
        ancestor_list = []
        this_parent = self.parent
        
        # append
        while this_parent:
            ancestor_list.append(this_parent)
            this_parent = this_parent.parent
            
        #Step 2.
        rels = {}
        rt_set = Relation.objects.all()
        right_subset = []
        left_subset = []
        
        for each in ancestor_list:
            # retrieve all the RT's from each ancestor 
            right_subset.extend(rt_set.filter(subject1=each.id))
            left_subset.extend(rt_set.filter(subject2=each.id))
         
        rels['possible_leftroles'] = left_subset
        rels['possible_rightroles'] = right_subset
        
        return rels


    def get_possible_attributes(self):
        """
        Gets the relations possible for this metatype
        1. Recursively create a set of all the ancestors i.e. parent/subtypes of the MT. 
        2. Get all the RT's linked to each ancestor 
        """
        #Step 1. 
        ancestor_list = []
        this_parent = self.parent
        
        # recursive thru parent field and append
        while this_parent:
            ancestor_list.append(this_parent)
            this_parent = this_parent.parent
            
        #Step 2.
        attrs = [] 
                
        for each in ancestor_list:
            # retrieve all the AT's from each ancestor 
            attrs.extend(Attribute.objects.filter(subject=each.id))
                     
        return attrs




    @property
    def get_nbh(self):
        """ 
        Returns the neighbourhood of the object
        """
        fields = ['title','altname','pluralform']
        nbh = {}
        nbh['title'] = self.title        
        nbh['altnames'] = self.altnames                
        nbh['plural'] = self.plural
        nbh['content'] = self.content
        #return  all OTs the object is linked to
        nbh['member_of'] = self.objecttypes.all()
        
        # get all the relations of the object    
        nbh.update(self.get_relations())
        nbh.update(self.get_attributes())
        # encapsulate the dictionary with its node name as key
        return nbh

    
    def get_graph_json(self):

        predicate_id={"plural":"a1","altnames":"a2","member_of":"a3"}
	g_json = {}
	g_json["node_metadata"]= [] 
	
	
	nbh = self.get_nbh
	
        this_node = {"_id":str(self.id),"title":self.title,"screen_name":self.title, "url":self.get_absolute_url()}
	for key in predicate_id.keys():
		if nbh[key]:
			try:
				g_json[str(key)]=[]      
				g_json["node_metadata"].append({"_id":str(predicate_id[key]),"screen_name":key})
				g_json[str(key)].append({"from":self.id , "to":predicate_id[key],"value":1  })
				if not isinstance(nbh[key],basestring):
					for item in nbh[key]:
				
						g_json["node_metadata"].append({"_id":str(item.id),"screen_name":item.title, "title":item.title, "url":item.get_absolute_url()})
						g_json[str(key)].append({"from":predicate_id[key] , "to":item.id ,"value":1  })
			
				else:
					value={nbh["plural"]:"a4",nbh["altnames"]:"a5"}			
		            		this_node[str(key)]=nbh[key]
				
					for item in value.keys():
						g_json["node_metadata"].append({"_id":str(value[nbh[key]]),"screen_name":nbh[key]})
						g_json[str(key)].append({"from":predicate_id[key] , "to":value[nbh[key]] ,"value":1  })
				
			
			except:
		                    pass
	g_json["node_metadata"].append(this_node)      
        return json.dumps(g_json)   


    @property
    def get_relations1(self):
        """
        Returns all the relations of the nodetype
        """
        relations={}
        reltype={}
        left_relations=Relation.objects.filter(left_subject=self.id)
        if left_relations:
           for each in left_relations:
           	relation=each.relationtype.title
           	predicate=each.right_subject
           	predicate_values=[]
                if reltype:
              	   for key,value in reltype.items():
                       predicate_values=value
                       if each.relationtype.title==key:
                          predicate_values.append(predicate)
                          reltype[key]=predicate_values
                          break
                       else:
                          predicate_values=predicate
                          reltype[relation]=predicate_values
                          break
                else:
                    predicate_values.append(predicate)
                    reltype[relation]=predicate_values
                relations['lrelations']=reltype
        
        right_relations=Relation.objects.filter(right_subject=self.id)
        reltype={}
        if right_relations:
           for each in right_relations:
           	relation=each.relationtype.inverse
           	predicate=each.left_subject
                predicate_values=[]
                if reltype:
              	   for key,value in reltype.items():
                       predicate_values=value
                       if each.relationtype.inverse==key:
                          predicate_values.append(predicate)
                          reltype[key]=predicate_values
                          break
                       else:
                          predicate_values=predicate
                          reltype[relation]=predicate_values
                          break
                else:
                   predicate_values.append(predicate)
                   reltype[relation]=predicate_values
                relations['rrelations']=reltype
        return relations
    @property
    def get_rendered_nbh(self):
        """ 
        Returns the neighbourhood of the object
        """
        fields = ['title','altname','pluralform']
        nbh = {}
        nbh['title'] = self.title        
        nbh['altnames'] = self.altnames                
        nbh['plural']=self.plural
        nbh['content'] = self.content
        #return  all OTs the object is linked to
        member_of_dict = {}
        for each in self.objecttypes.all():
            member_of_dict[each.title]= each.get_absolute_url()
        nbh['member_of']=member_of_dict
        #get Relations
        relns={}
        rellft={}
        relrgt={}
        if self.get_relations1:
            NTrelns=self.get_relations1
            for key,value in NTrelns.items():
                if key=="rrelations":
                    relrgt={}
                    for rgtkey,rgtvalue in value.items():
                        relnvalue={}
                        if isinstance(rgtvalue,list):
                            for items in rgtvalue:
                                relnvalue[items]=items.get_absolute_url()
                        else:
                            relnvalue[rgtvalue]=rgtvalue.get_absolute_url()
                        
                        relrgt[rgtkey]=relnvalue
                    
                else:
                    rellft={}
                    relns['left']=rellft
                    for lftkey,lftvalue in value.items():
                        relnvalue={}
                        if isinstance(lftvalue,list):
                             for items in lftvalue:
                                 relnvalue[items]=items.get_absolute_url()
                        else:
                             relnvalue[lftvalue]=lftvalue.get_absolute_url()
                        
                        rellft[lftkey]=relnvalue
                    
        nbh['relations']=relrgt
        nbh['relations'].update(rellft)
   
        #get Attributes
        attributes ={}
        for each in self.subject_of.all():
             attributes[each.attributetype]=each.svalue 
        nbh['attributes']=attributes
        return nbh



    @property
    def html_content(self):
        """Return the content correctly formatted"""
        if MARKUP_LANGUAGE == 'markdown':
            return markdown(self.content, MARKDOWN_EXTENSIONS)
        elif MARKUP_LANGUAGE == 'textile':
            return textile(self.content)
        elif MARKUP_LANGUAGE == 'restructuredtext':
            return restructuredtext(self.content)
        elif not '</p>' in self.content:
            return linebreaks(self.content)
        return self.content


    @property
    def previous_gbobject(self):
        """Return the previous gbobject"""
        gbobjects = Gbobject.published.filter(
            creation_date__lt=self.creation_date)[:1]
        if gbobjects:
            return gbobjects[0]

    @property
    def next_gbobject(self):
        """Return the next gbobject"""
        gbobjects = Gbobject.published.filter(
            creation_date__gt=self.creation_date).order_by('creation_date')[:1]
        if gbobjects:
            return gbobjects[0]

    @property
    def word_count(self):
        """Count the words of an gbobject"""
        return len(strip_tags(self.html_content).split())

    @property
    def is_actual(self):
        """Check if an gbobject is within publication period"""
        now = datetime.now()
        return now >= self.start_publication and now < self.end_publication

    @property
    def is_visible(self):
        """Check if an gbobject is visible on site"""
        return self.is_actual and self.status == PUBLISHED

    @property
    def related_published(self):
        """Return only related gbobjects published"""
        return gbobjects_published(self.related)

    @property
    def discussions(self):
        """Return published discussions"""
        return comments.get_model().objects.for_model(
            self).filter(is_public=True)

    @property
    def comments(self):
        """Return published comments"""
        return self.discussions.filter(Q(flags=None) | Q(
            flags__flag=CommentFlag.MODERATOR_APPROVAL))

    @property
    def pingbacks(self):
        """Return published pingbacks"""
        return self.discussions.filter(flags__flag='pingback')

    @property
    def trackbacks(self):
        """Return published trackbacks"""
        return self.discussions.filter(flags__flag='trackback')

    @property
    def comments_are_open(self):
        """Check if comments are open"""
        if AUTO_CLOSE_COMMENTS_AFTER and self.comment_enabled:
            return (datetime.now() - self.start_publication).days < \
                   AUTO_CLOSE_COMMENTS_AFTER
        return self.comment_enabled

    @property
    def short_url(self):
        """Return the gbobject's short url"""
        return get_url_shortener()(self)

    def __unicode__(self):
        return self.title

    @property
    def memberof_sentence(self):
        """Return the objecttype of which the gbobject is a member of"""
        
        if self.objecttypes.count:
            for each in self.objecttypes.all():
                return '%s is a member of objecttype %s' % (self.title, each)
        return '%s is not a fully defined name, consider making it a member of a suitable objecttype' % (self.title)


    @models.permalink
    def get_absolute_url(self):
        """Return gbobject's URL"""
        return ('objectapp_gbobject_detail', (), {
            'year': self.creation_date.strftime('%Y'),
            'month': self.creation_date.strftime('%m'),
            'day': self.creation_date.strftime('%d'),
            'slug': self.slug})

    class Meta:
        """Gbobject's Meta"""
        ordering = ['-creation_date']
        verbose_name = _('object')
        verbose_name_plural = _('objects')
        permissions = (('can_view_all', 'Can view all'),
                       ('can_change_author', 'Can change author'), )



class Process(Gbobject):    

    """
    A store processes, events or changes described as changes in attributes and relations
    """
    processtypes = models.ManyToManyField(Processtype, verbose_name=_('member of process type'),
                                          related_name='member_processes',
                                          blank=True, null=True)
    priorstate_attribute_set = models.ManyToManyField(Attribute, null=True, blank=True,
                                                      verbose_name=_('in prior state attribute set of'),
                                                      related_name='in_prior_state_attrset_of')
    priorstate_relation_set = models.ManyToManyField(Relation, null=True, blank=True,
                                                     verbose_name=_('priorsate of relation set'),
                                                     related_name='in_prior_state_relset_of')

    poststate_attribute_set = models.ManyToManyField(Attribute, null=True, blank=True,
                                                     verbose_name=_('poststate of attribute set'),
                                                     related_name='in_post_state_attrset_of')

    poststate_relation_set = models.ManyToManyField(Relation, null=True, blank=True,
                               verbose_name=_('in poststate of relation set'),
                               related_name='in_post_state_relset_of')




    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name = _('process')
        verbose_name_plural = _('processes')
        permissions = (('can_view_all', 'Can view all'),
                       ('can_change_author', 'Can change author'), )


class System(Gbobject):    

    """
    instance of a Systemtype
    """

    systemtypes = models.ManyToManyField(Systemtype, verbose_name=_('member of systemtype'),
                                        related_name='member_systems',
                                         blank=True, null=True)

    gbobject_set = models.ManyToManyField(Gbobject, related_name="in_gbobject_set_of", 
                                       verbose_name='objects in the system',    
                                       blank=True, null=False) 

    relation_set = models.ManyToManyField(Relation, related_name="in_relation_set_of", 
                                         verbose_name='relations in the system',    
                                         blank=True, null=False) 

    attribute_set = models.ManyToManyField(Attribute, related_name="in_attribute_set_of", 
                                          verbose_name='attributes in the system',
                                          blank=True, null=False)

    process_set = models.ManyToManyField(Process, related_name="in_process_set_of", 
                                        verbose_name='processes in the system',    
                                        blank=True, null=False) 

    system_set = models.ManyToManyField('self', related_name="in_system_set_of", 
                                       verbose_name='nested systems',
                                       blank=True, null=False)


    def __unicode__(self):
        return self.title


    
if not reversion.is_registered(Process):
    reversion.register(Process, follow=["priorstate_attribute_set", "priorstate_relation_set", "poststate_attribute_set", "poststate_relation_set", "prior_nodes", "posterior_nodes"])

if not reversion.is_registered(System): 
    reversion.register(System, follow=["systemtypes", "gbobject_set", "relation_set", "attribute_set", "process_set", "system_set", "prior_nodes", "posterior_nodes"])

if not reversion.is_registered(Gbobject):
    reversion.register(Gbobject, follow=["objecttypes", "prior_nodes", "posterior_nodes"])


moderator.register(Gbobject, GbobjectCommentModerator)

post_save.connect(ping_directories_handler, sender=Gbobject,
                  dispatch_uid='objectapp.gbobject.post_save.ping_directories')
post_save.connect(ping_external_urls_handler, sender=Gbobject,
                  dispatch_uid='objectapp.gbobject.post_save.ping_external_urls')


