from google.appengine.ext import db
from google.appengine.api import users
from datetime import time as datetime_time

class UserPrefs(db.Model):
    user = db.UserProperty()

def getUserPrefs():
    user = users.get_current_user()
    if user:
        q = db.GqlQuery("SELECT * FROM UserPrefs WHERE user = :1", user)
        return q.get()
                
class Feed(db.Model):
    user = db.UserProperty(required=True)

    title = db.StringProperty(required=True)
    link_web = db.StringProperty(required=True)
    link_rss = db.StringProperty(required=True)
    #hub = db.StringProperty(default=None) # pubsubhubbub link

    date_added = db.DateProperty(auto_now_add=True)
    date_last_crawled = db.DateTimeProperty(auto_now_add=True)
    date_last_email = db.DateTimeProperty()
    
    # bitfild of days to send digest (Mo=1, Tue=2, Wed=4, ...) or 0=instant
    digest_days = db.IntegerProperty(default=0) 
    digest_time = db.TimeProperty(default=datetime_time(12, 0))

class FeedItemNew(db.Model):
    """Feed entries before email was sent"""
    feed = db.ReferenceProperty(Feed)

    title = db.StringProperty(required=True)
    link = db.StringProperty(required=True)    
    date_added = db.DateProperty(auto_now_add=True)

class FeedItemSent(db.Model):
    """Feed entries after email was sent, moved from FeedItemNew"""
    feed = db.ReferenceProperty(Feed)

    title = db.StringProperty(required=True)
    link = db.StringProperty(required=True)
    date_added = db.DateProperty(auto_now_add=True)
    
    email_sent = db.BooleanProperty(default=False)    
