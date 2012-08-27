from five import grok
from plone.directives import dexterity, form

from zope import schema
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm

from zope.interface import invariant, Invalid

from z3c.form import group, field

from plone.namedfile.interfaces import IImageScaleTraversable
from plone.namedfile.field import NamedImage, NamedFile
from plone.namedfile.field import NamedBlobImage, NamedBlobFile

from plone.app.textfield import RichText

from z3c.relationfield.schema import RelationList, RelationChoice
from plone.formwidget.contenttree import ObjPathSourceBinder, UUIDSourceBinder

from Products.CMFCore.utils import getToolByName
from Acquisition import aq_inner
from zope.component import getMultiAdapter
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from zope.app.container.interfaces import IObjectAddedEvent
from zope.lifecycleevent.interfaces import IObjectModifiedEvent
from encryption_tag import IEncryptionTag

import json
import re

from zope.component import getUtility
from plone.dexterity.interfaces import IDexterityFTI
from zope.schema import getFieldsInOrder

from plone.app.workflow.browser.sharing import SharingView

from collective.encrypted import MessageFactory as _

"""
Utility class for holding commonly used stuff.
"""
class PageUtils:
    keyquery_template = ViewPageTemplateFile("encrypted_page_templates/keyquery.pt")

    def querykeys(self):
     """
      Returns the key query template, which is used for querying missing encryption keys.
     """
     return self.keyquery_template()

    @staticmethod
    @grok.provider(IContextSourceBinder)
    def possibleTags(context):
     """
     Returns a vocabulary for schema.Choice (the encryption tag selection). Takes into account the user permissions for tags.
     """
     tags = []
     catalog = getToolByName(context, 'portal_catalog')
     results = catalog(portal_type='collective.encrypted.encryptiontag')
     if results is not None:
      for tag in results:
       tags.append(SimpleVocabulary.createTerm(tag.UID, str(tag.UID), tag.Title))
     return SimpleVocabulary(tags)

    def tags(self):
     """
     Returns a dict containing the tag objects the page is referring to. Will take the list of tag UIDs from context.
     """
     tags = {}
     if (self.context and self.context.encryptedtags):
      for tag in self.context.encryptedtags: # tag will contain string representation of UID
       tags[tag] = self.getByUUID(tag) # fetching the object
     return tags

    def getByUUID(self,uuid):
     """
     Returns any content by the UID field.
     """
     context = aq_inner(self.context)
     tools = getMultiAdapter((self.context, self.request), name=u'plone_tools')
     portal_url = tools.catalog()
     results = portal_url(UID=uuid)
     if not results or results.actual_result_count!=1:
      raise Exception('Unable to find content by UID '+uuid)
     return results[0].getObject()

    """
    Returns a string containing simple list of the tags used in the content. Used in view template.
    """
    def tagsfortitle(self):
     taglist = ""
     tags = self.tags()
     for key in tags.keys():
      tag = tags[key]
      taglist += tag.title + " "
     return taglist

    """
    Returns json version of the tags used in content. Assumes that the IBasic prodided fields are present.
    """
    def tagsjson(self):
     output = []
     tags = self.tags()
     for key in tags.keys(): # Iterate through all tags
      tag = tags[key]
      output.append({"title":tag.title,"UID":key})
     return json.dumps(output)

    """  
    Validates the iv field
    """
    @staticmethod
    def validateIV(value):
     return re.match("^[0-9a-f]{32,32}$",value)

    """
    Validates the content field
    """
    @staticmethod
    def validateContent(value):
     # TinyMCE forcibly wraps the field in p, otherwise it's a hex string
     return re.match("^<p>[0-9a-f]+</p>$",value.raw)



# Interface class; used to define content-type schema.

class IEncryptedpage(form.Schema, IImageScaleTraversable):
    """
    Encrypted page
    """
    encryptedcontent = RichText(
            title=_(u"Content"),
            required=True,
            constraint=PageUtils.validateContent,
        )
    encryptedtags = schema.List(
            title=_(u"Encryption tags"),
            default=[],
            value_type=schema.Choice(title=_(u"Tags"),source=PageUtils.possibleTags),
            required=True,
        )
    encryptediv = schema.TextLine(
            title=_(u"Initialization vector"),
            required=True,
            constraint=PageUtils.validateIV,
        )



# Custom content-type class; objects created for this content type will
# be instances of this class. Use this class to add content-type specific
# methods and properties. Put methods that are mainly useful for rendering
# in separate view classes.

class Encryptedpage(dexterity.Item):
    grok.implements(IEncryptedpage)
    
    # Add your class methods and properties here


# View class
# The view will automatically use a similarly named template in
# encrypted_page_templates.
# Template filenames should be all lower case.
# The view will render when you request a content object with this
# interface with "/@@sampleview" appended.
# You may make this the default view for content objects
# of this type by uncommenting the grok.name line below or by
# changing the view class name and template filename to View / view.pt.

class View(grok.View,PageUtils):
    grok.context(IEncryptedpage)
    grok.require('zope2.View')

class Add(dexterity.AddForm,PageUtils):
    grok.context(IEncryptedpage)
    grok.name("collective.encrypted.encryptedpage")

    def updateWidgets(self):
     super(Add, self).updateWidgets()
     self.widgets["encryptediv"].mode="hidden"

class Edit(dexterity.EditForm,PageUtils):
    grok.context(IEncryptedpage)

    def updateWidgets(self):
     super(Edit, self).updateWidgets()
     self.widgets["encryptediv"].mode = "hidden"

