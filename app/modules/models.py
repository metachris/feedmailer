from google.appengine.ext import db
from google.appengine.api import users
from datetime import time as datetime_time

class UserPrefs(db.Model):
    user = db.UserProperty(required=True)
    
    date_joined = db.DateTimeProperty(auto_now_add=True)    
    date_lastlogin = db.DateTimeProperty(auto_now_add=True)    
    emails_received = db.IntegerProperty(default=0)

    # If true, all feeds will be combined into one digest,
    # if false every feed is delivered in a separate email.
    combined_digest = db.BooleanProperty(default=True)

    # if items are ready to be sent by email
    # ~ user.feeditem_set.count() > 0
    _items_ready = db.BooleanProperty(default=False)
    
    # Next scheduled email sending
    _digest_next = db.DateTimeProperty()
    
def getUserPrefs(user):
    """Get or create user preference object"""
    if user:
        q = db.GqlQuery("SELECT * FROM UserPrefs WHERE user = :1", user)
        prefs = q.get()
        if not prefs:
            prefs = UserPrefs(user=user)
            prefs.put()
        return prefs

class UserDigestInterval(db.Model):
    """One user can have multiple interval groups. Multiple feeds can
    use the same interval group which, when updated, affects all feeds"""
    user = db.UserProperty(required=True)    
    title = db.StringProperty(required=True)
    
    digest_days = db.IntegerProperty(default=0)
    digest_time = db.TimeProperty(default=datetime_time(12, 0))

def getUserDigestIntervals(user):
    """Get or create digest interval object"""
    if user:
        q = db.GqlQuery("SELECT * FROM UserDigestInterval WHERE user = :1", user)
        d = q.get()
        if not d:
            d = UserDigestInterval(user=user, title="Standard")
            d.put()
        return d

class Feed(db.Model):
    user = db.UserProperty(required=True)
    title = db.StringProperty(required=True)
    link_web = db.StringProperty(required=True)
    link_rss = db.StringProperty(required=True)
    #link_hub = db.StringProperty(default=None) # pubsubhubbub link
    
    date_added = db.DateProperty(auto_now_add=True)
    date_last_crawled = db.DateTimeProperty(auto_now_add=True)
    
    # digest timing can either be a group or a custom setting.
    # if digest_group == None: use custom settings, 
    # else: use group and overwrite custom settings with group settings 
    #      (needed for querying feeds that need to send emails)
    digest_group = db.ReferenceProperty(UserDigestInterval)
    
    # bitfild of days to send digest (Mo=1, Tue=2, Wed=4, ...) or 0=instant
    digest_days = db.IntegerProperty(default=0) 
    digest_time = db.TimeProperty(default=datetime_time(12, 0))

    # last email and when next is scheduled. updated with either
    # 1. digest interval update by user on web
    # 2. when next email was sent by system  
    _digest_next = db.DateTimeProperty()
    
class FeedItem(db.Model):
    """Feed item waiting to be sent to the user on next delivery interval"""
    feed = db.ReferenceProperty(Feed, required=True)
    user = db.UserProperty(required=True)
    title = db.StringProperty(required=True)
    link = db.StringProperty(required=True)
        
    date_added = db.DateProperty(auto_now_add=True)
