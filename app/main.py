#!/usr/bin/env python

import os

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template

from google.appengine.ext import db

class UserPrefs(db.Model):
    user = db.UserProperty()

def getUserPrefs():
    user = users.get_current_user()
    if user:
        q = db.GqlQuery("SELECT * FROM UserPrefs WHERE user = :1", user)
        return q.get()
                
class Feed(db.Model):
    name = db.StringProperty(required=True)
    uri = db.StringProperty(required=True)
    digest_type = db.IntegerProperty()
    user = db.UserProperty(required=True)
    date_added = db.DateProperty(auto_now_add=True)
    last_read = db.DateProperty()

class FeedItem(db.Model):
    title = db.StringProperty(required=True)
    uri = db.StringProperty(required=True)
    date_added = db.DateProperty(auto_now_add=True)
    email_sent = db.BooleanProperty()    
    feed = db.ReferenceProperty(Feed)

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
        o = ""
        for feed in feeds:
            o += "- %s<br>" % feed.name

        template_values = {
            'nick': user.nickname(), 
            'url': url,
            'url_linktext': url_linktext,
            'feeds': feeds,
            'o': o
            }
                                    
        path = os.path.join(os.path.dirname(__file__), 'templates/feeds.html')
        self.response.out.write(template.render(path, template_values))        

    def post(self):
        user = users.get_current_user() 
        #self.response.out.write(self.request.get('uri') )
        #return
        feed = Feed(user=user, name=self.request.get('uri'), uri=self.request.get('uri'))
        feed.put()
        
        i = Feed.all()
        for f in i:
            print "-",f.name
            
        #self.response.out.write("saved")
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