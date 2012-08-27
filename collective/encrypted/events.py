from five import grok
from Products.CMFCore.utils import getToolByName
from encrypted_page import IEncryptedpage
from zope.app.container.interfaces import IObjectAddedEvent
from zope.lifecycleevent.interfaces import IObjectModifiedEvent
from encryption_tag import IEncryptionTag
from plone.uuid.interfaces import IUUID

@grok.subscribe(IEncryptedpage, IObjectAddedEvent)
@grok.subscribe(IEncryptedpage, IObjectModifiedEvent)
def assignRights(page, event):
   """
   Will change the access rights of a page automatically to a generated set.
   """
   tags = gettags(page)
   acl = combineAcls(tags)
   # Set the ACLS
   setattr(page, '__ac_local_roles_block__','True')
   page.__ac_local_roles__ = acl
   page.reindexObject()


@grok.subscribe(IEncryptionTag, IObjectAddedEvent)
@grok.subscribe(IEncryptionTag, IObjectModifiedEvent)
def updateTagRights(tag, event):
   """
   If a user modifies an encryption tag all the content items using that tag will have their access rights also updated.
   """
   pages = []
   context = tag.aq_base
   uuid = IUUID(context, None)

   catalog = getToolByName(tag, 'portal_catalog')
   results = catalog.searchResults({"encryptedtags":uuid})
   
   for result in results:
     object = result.getObject()
     assignRights (object, event) 

def gettags(page):
 """
 Returns the tags used in page. If a referred tag is missing will omit the tag.
 """
 tags = []
 catalog = getToolByName(page, 'portal_catalog')
 names = page.encryptedtags
 for name in names:
  results = catalog.searchResults({'UID':name})
  if results and len(results)>0:
   result = results[0].getObject()
   tags.append(result)
 return tags


def combineAcls(tags):
  """
  Builds the ACL to be assigned on the page. User will get access rights if he holds at least some access right to all of the tags.
  The access right level is copied from all the tags in that case. This is a middle road between demanding 1:1 similar access rights on all tags 
  or just and'ing them all together without taking into account that user has no right to one of the tags.
  """
  counts = countRefers(tags)
  dicts = [] # ACL dicts of all tags
  for tag in tags:
   dicts.append(tag.__ac_local_roles__)
  # Let's build the final acl
  combined = combineDicts(dicts,counts)
  return combined

def countRefers(tags):
  """
  Counts how many times a certain username / groupname is mentioned in the local role assignments
  """
  count = {}
  for tag in tags:
   roles = tag.__ac_local_roles__
   for key in roles.keys():
    if key in count:
     count[key] += 1 
    else:
     count[key] = 1
  return count

def combineDicts(dicts,counts):
  """
  For every key that is found from all dicts, combine the contents of assignment array.
  """
  result = {} 
  for key in counts.keys():
   if counts[key]==len(dicts):
    # The key has at least some role in all dicts. Iterate through all dicts, and combine the access rights for that key
    combined = []
    for dict in dicts:
     combined += dict[key] 
    combined = list(set(combined)) 
    result[key] = combined
  return result

