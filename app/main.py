#!/usr/bin/env python

import os

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db

from lib import feedparser

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

        path = os.path.join(os.path.dirname(__file__), 'templates/index.html')
        self.response.out.write(template.render(path, template_values))        

class FeedsPage(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user() 
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'

        feeds = db.GqlQuery("SELECT * FROM Feed WHERE user = :1 ORDER BY date_added DESC", user)

        template_values = {
            'username': user.nickname(), 
            'url': url,
            'url_linktext': url_linktext,
            'feeds': feeds,
            }
                                    
        path = os.path.join(os.path.dirname(__file__), 'templates/feeds.html')
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
            feed = Feed(user=user, title=f.feed.title, link=f.feed.link)
            feed.put()
            
        self.redirect("/feeds")
        return 




application = webapp.WSGIApplication([
                                    ('/', MainPage),
                                    ('/feeds', FeedsPage)
                                     ],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()