from plone.app.workflow.browser.sharing import SharingView
from zope.lifecycleevent import ObjectModifiedEvent
import zope.event

AUTH_GROUP = 'AuthenticatedUsers'
STICKY = (AUTH_GROUP, )

def merge_search_results(results, key):
    """Merge member search results.

    Based on PlonePAS.browser.search.PASSearchView.merge.
    """
    output={}
    for entry in results:
        id=entry[key]
        if id not in output:
            output[id]=entry.copy()
        else:
            buf=entry.copy()
            buf.update(output[id])
            output[id]=buf

    return output.values()

class NotifySharingView(SharingView):

    def __call__(self):
      result = super(NotifySharingView, self).__call__()
      if (self.context.portal_type == "collective.encrypted.encryptedpage"):
        event = ObjectModifiedEvent(self.context)
        zope.event.notify(event)
      if (self.context.portal_type == "collective.encrypted.encryptiontag"):
        event = ObjectModifiedEvent(self.context)
        zope.event.notify(event)
      return result

