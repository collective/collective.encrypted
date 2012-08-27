from Products.CMFPlone.utils import isLinked
from ZPublisher.HTTPRequest import HTTPRequest
from ZPublisher.HTTPResponse import HTTPResponse
from collective.encrypted import MessageFactory as _
from Products.CMFPlone.utils import safe_unicode
from Products.CMFPlone.utils import transaction_note
from zope.interface import Interface
from five import grok
from Products.statusmessages.interfaces import IStatusMessage
from encryption_tag import TagUtils
from Products.CMFCore.utils import getToolByName
from Products.CMFDefault.exceptions import ResourceLockedError

# This stuff is aped from CMFPlone/skins/plone_scripts/folder_delete.cpy
class DeleteUtils:

     def hasChildrenReferencing(self,object,messages):
       result = False
       all = self.__getChildren(object)
       for content in all:
         if content.portal_type == "collective.encrypted.encryptiontag" and self.hasReferences(content,self.request):
          messages.add(_(u"Tag "+str(content.Title())+" is still in use, unable to delete!"), type=u"error")
          result = True
       return result

     def __getChildren(self,context):
       items = []
       items.append(context)
       if context.hasChildNodes():
         children = context.getChildNodes()
         for child in children:
          items += self.__getChildren(child)
       return items

     def hasReferences(self):
       utils = TagUtils()
       users = utils.getUsers(self.context, self.request)
       if len(users)>0:
         return True
       else:
         return False

     def hasReferences(self,content,request):
       utils = TagUtils()
       users = utils.getUsers(content,request)
       if len(users)>0:
         return True
       else:
         return False

# This stuff is aped from CMFPlone/skins/plone_form_scripts/delete_confirmation.cpy
class DeleteFolder(grok.View,DeleteUtils):
     grok.context(Interface)
     grok.require('zope2.DeleteObjects')

     def update(self):
       putils = self.context.plone_utils
       request = self.request
       locked = []
       other = []
       paths=request.get('paths', [])
       messages = IStatusMessage(self.request)
       self.context.REQUEST.set('link_integrity_events_to_expect', len(paths))

       catalog = getToolByName(self.context, 'portal_catalog')

       references = False
       for path in paths:
         results = catalog.searchResults({'path':path})
         for result in results:
          object = result.getObject()
          if self.hasChildrenReferencing(object,messages):
           references = True
        
       if not references: 
        success, failure = putils.deleteObjectsByPaths(paths, REQUEST=request)
        
        if success:
          messages.add(_(u'Item(s) deleted.'), type=u"info")
        if failure:
          for key, value in failure.items():
            try:
              raise value
            except ResourceLockedError:
              locked.append(key)
            except:
              other.append(key)
            else:
              other.append(key)
        mapping = {}
        if locked:
          mapping[u'lockeditems'] = ', '.join(locked)
          message = _(u'These items are locked for editing: ${lockeditems}.', mapping=mapping)
          messages.add(message, type=u"error")
        if other:
          mapping[u'items'] = ', '.join(other)
          message = _(u'${items} could not be deleted.', mapping=mapping)
          messages.add(message, type=u"error")

       self.response.redirect("/".join(self.context.getPhysicalPath())+"/")       

class Sdelete(grok.View,DeleteUtils):
     grok.context(Interface)
     grok.require('zope2.DeleteObjects')

     def update(self):
      messages = IStatusMessage(self.request)
      request = self.request
      if (request['REQUEST_METHOD'] == "POST"):
       cancel = False
       for item in request.form.items():
        if ("form.button.Cancel" in item):
         cancel = True
       if (cancel==False):
         #"self.hasChildrenReferencing(self.context,messages)
         if (self.context.portal_type == "collective.encrypted.encryptiontag" and self.hasReferences(self.context,self.request)):
           messages.add(_(u"Tag is still in use, unable to delete!"), type=u"error")
         else:          
           if not self.hasChildrenReferencing(self.context,messages):
             self.__delete() 

     def __delete(self):
      context = self.context
      parent = context.aq_inner.aq_parent
      pp = "/".join(parent.getPhysicalPath())+"/"
      title = safe_unicode(context.title_or_id())

      try:
       lock_info = context.restrictedTraverse('@@plone_lock_info')
      except AttributeError:
       lock_info = None

      if lock_info is not None and lock_info.is_locked():
       message = _(u'${title} is locked and cannot be deleted.',
                 mapping={u'title' : title})
       messages.add(message, type=u"info")
      else:
       parent.manage_delObjects(context.getId())
       message = _(u'${title} has been deleted.',
                      mapping={u'title' : title})
       transaction_note('Deleted %s' % context.absolute_url())
       IStatusMessage(self.request).addStatusMessage(message, type='info')

      # There is a bug in Plone that will actually cause the message to be lost, sorry
      self.response.redirect(pp)
