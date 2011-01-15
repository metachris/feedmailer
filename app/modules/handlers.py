import os

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

from models import *

from lib import feedparser

class MainPage(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user() 
        if user:
            self.redirect("/feeds")
            return 
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
            greeting = "Hi"

        template_values = {
            'greeting': greeting,
            'url': url,
            'url_linktext': url_linktext,
            }

        path = os.path.join(os.path.dirname(__file__), '../templates/index.html')
        self.response.out.write(template.render(path, template_values))        

class FeedsPage(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user() 
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'

        feeds = db.GqlQuery("SELECT * FROM Feed WHERE user = :1 ORDER BY date_added DESC", user)

        template_values = {
            'user': user,
            'username': user.nickname(), 
            'url': url,
            'url_linktext': url_linktext,
            'feeds': feeds,
            }
                                    
        path = os.path.join(os.path.dirname(__file__), '../templates/feeds.html')
        self.response.out.write(template.render(path, template_values))        

    def post(self):
        user = users.get_current_user()
         
        link = self.request.get('uri')
        if link and len(link) > 0:
            f = feedparser.parse(link)

            # Check for valid feed            
            if not f.feed.has_key("title"):
                self.redirect("/feeds?i=%s" % link)
                return 
            
            # Check if already in list
            feed = db.GqlQuery("SELECT * FROM Feed WHERE user = :1 AND link = :2 ORDER BY date_added DESC", user, f.feed.link)
            if feed.count() > 0:
                self.redirect("/feeds?d=%s" % link)
                return 
                    
            # Valid feed, add to list
            feed = Feed(user=user, title=f.feed.title, link_web=f.feed.link, link_rss=f.href)
            feed.put()
            
            # Store all entries in DB
            for entry in f.entries:
                item = FeedItemNew(feed=feed, title=entry.title, link=entry.link)
                item.put()
                
        self.redirect("/feeds/update/%s" % feed.key())
        return 


class FeedSettings(webapp.RequestHandler):
    def get(self, key):
        user = users.get_current_user()

        feeds = db.GqlQuery("SELECT * FROM Feed WHERE __key__ = :1", db.Key(key))
        
        template_values = {
            'user': user,
            'feed': feeds.fetch(1)[0],
            }
                                    
        path = os.path.join(os.path.dirname(__file__), '../templates/feeds_settings.html')
        self.response.out.write(template.render(path, template_values))        

