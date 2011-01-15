from google.appengine.ext import db
from google.appengine.api import users

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
    link = db.StringProperty(required=True)
    hub = db.StringProperty(default=None)   # pubsubhubbub link
    #type = db.StringProperty() # rss, atom, etc

    date_added = db.DateProperty(auto_now_add=True)
    date_last_crawled = db.DateProperty()
    
    digest_type = db.IntegerProperty()

class FeedItem(db.Model):
    feed = db.ReferenceProperty(Feed)

    title = db.StringProperty(required=True)
    link = db.StringProperty(required=True)
    
    date_added = db.DateProperty(auto_now_add=True)
    email_sent = db.BooleanProperty(default=False)    
