from five import grok
from plone.directives import dexterity, form

from zope import schema
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm

from zope.interface import invariant, Invalid, Interface

from z3c.form import group, field

from plone.namedfile.interfaces import IImageScaleTraversable
from plone.namedfile.field import NamedImage, NamedFile
from plone.namedfile.field import NamedBlobImage, NamedBlobFile

from plone.app.textfield import RichText

from z3c.relationfield.schema import RelationList, RelationChoice
from plone.formwidget.contenttree import ObjPathSourceBinder

from collective.encrypted import MessageFactory as _

from Acquisition import aq_inner
from zope.component import getMultiAdapter
from plone.uuid.interfaces import IUUID

# Interface class; used to define content-type schema.

class IEncryptionTag(form.Schema, IImageScaleTraversable):
    """
    Encryption key helper for encrypted pages
    """
    
    # If you want a schema-defined interface, delete the form.model
    # line below and delete the matching file in the models sub-directory.
    # If you want a model-based interface, edit
    # models/encryption_tag.xml to define the content type
    # and add directives here as necessary.
    
    form.model("models/encryption_tag.xml")


# Custom content-type class; objects created for this content type will
# be instances of this class. Use this class to add content-type specific
# methods and properties. Put methods that are mainly useful for rendering
# in separate view classes.

class EncryptionTag(dexterity.Item):
    grok.implements(IEncryptionTag)
    
    # Add your class methods and properties here

class TagUtils:
    def users(self):
     return self.getUsers(self.context, self.request)

    def getUsers(self,item,request):
     """
     Will return the pages that are using this tag
     """
     context = aq_inner(item)
     tools = getMultiAdapter((context, request), name=u'plone_tools')
     portal_url = tools.catalog()
     id = self.getUID(context)
     results = portal_url({"encryptedtags":id})
     return results

    def getUID(self,item):
     """ AT and Dexterity compatible way to extract UID from a content item """
     # Make sure we don't get UID from parent folder accidentally
     context = item.aq_base
     # Returns UID of the context or None if not available
     # Note that UID is always available for all Dexterity 1.1+
     # content and this only can fail if the content is old not migrated
     uuid = IUUID(context, None)
     return uuid

# View class
# The view will automatically use a similarly named template in
# encryption_tag_templates.
# Template filenames should be all lower case.
# The view will render when you request a content object with this
# interface with "/@@sampleview" appended.
# You may make this the default view for content objects
# of this type by uncommenting the grok.name line below or by
# changing the view class name and template filename to View / view.pt.

class View(grok.View,TagUtils):
    grok.context(IEncryptionTag)
    grok.require('zope2.View')
    
    # grok.name('view')
