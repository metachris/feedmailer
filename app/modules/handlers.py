import os

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

from datetime import time as datetime_time

from lib import feedparser

from models import *
from tools import *

TEMPLATES_DIR = "../templates/"

class SignIn(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user() 
        url = users.create_login_url("/")
        self.redirect(url)

class SignOut(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user() 
        url = users.create_logout_url("/")
        self.redirect(url)

class Help(webapp.RequestHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), '%shelp.html' % TEMPLATES_DIR)
        self.response.out.write(template.render(path, None))        

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

        path = os.path.join(os.path.dirname(__file__), '%sindex.html' % TEMPLATES_DIR)
        self.response.out.write(template.render(path, template_values))        

class FeedsPage(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        user_prefs = getUserPrefs(user)
        user_dig = getUserDigestIntervals(user)
        
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'

        feeds = db.GqlQuery("SELECT * FROM Feed WHERE user = :1 ORDER BY date_added DESC", user)

        template_values = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
            'feeds': feeds,
        }
                                    
        path = os.path.join(os.path.dirname(__file__), '%sfeeds.html' % TEMPLATES_DIR)
        self.response.out.write(template.render(path, template_values))        

    def post(self):
        user = users.get_current_user()
         
        link = self.request.get('uri')
        if link and len(link) > 0:
            f = feedparser.parse(link)

            #if not f.status == 200:
            #    self.redirect("/feeds?s=%s&i=%s" % (f.status, link))
            #    return 

            # Check for valid feed            
            if not f.feed.has_key("title"):
                self.redirect("/feeds?i=%s" % link)
                return 
            
            # Check if already in list
            feed = db.GqlQuery("SELECT * FROM Feed WHERE user = :1 AND link_web = :2 ORDER BY date_added DESC", user, f.feed.link)
            if feed.count() > 0:
                self.redirect("/feeds?d=%s" % link)
                return 
                    
            # Valid feed, add to list
            feed = Feed(user=user, title=f.feed.title, link_web=f.feed.link, link_rss=f.href)

            # Append entries to "read" list to not send in next email
            # Reverse for adding newest items later, first items in _recent_items are oldest
            f.entries.reverse()
            for entry in f.entries:
                feed._recent_items.append(entry.link)
            while len(feed._recent_items) > 10:
                feed._recent_items.pop(0)

            feed.put()

            # Update User and Feed for _digest_next datetime 
            updateUserNextDigest(user, getUserPrefs(user))
                
            self.redirect("/feeds/update/%s" % feed.key())
            return

        else:
            self.redirect("/feeds?i=0")
            return 
             


class FeedSettings(webapp.RequestHandler):
    def get(self, key):
        user = users.get_current_user()

        feeds = db.GqlQuery("SELECT * FROM Feed WHERE __key__ = :1 AND user = :2", db.Key(key), user)
        feed = feeds.get() #fetch(1)[0]

        # map bitfield entries of digest_days to dictionary 0..6 [Mo..Sun]        
        days = {}
        for i in xrange(7):
            days[i] = feed.digest_days & (1<<i)
            
        template_values = {
            'user': user,
            'feed': feed,
            'days': days
        }
                                    
        path = os.path.join(os.path.dirname(__file__), '%sfeeds_settings.html' % TEMPLATES_DIR)
        self.response.out.write(template.render(path, template_values))        

    def post(self, key):
        user = users.get_current_user()

        #feeds = db.GqlQuery("SELECT * FROM Feed WHERE __key__ = :1 AND user = :2", db.Key(key), user)
        #feed = feeds.fetch(1)[0]
        feed = Feed.get(key)
        
        dt = self.request.get("dt")
        if dt and dt.index(":") > -1:
            hr, min = dt.split(":")
            feed.digest_time = datetime_time(int(hr), int(min))
                
        digest_type = self.request.get("d")
        if digest_type == "i":
            # instant digest
            feed.last_custom_digest_days = feed.digest_days
            feed.digest_days = 0

        elif digest_type == "c":
            days_bitfield = 0
            d = ["d0", "d1", "d2", "d3", "d4", "d5", "d6"]
            for i in xrange(len(d)):
                if self.request.get(d[i]): 
                    days_bitfield |= 1 << i
            if days_bitfield == 0:
                # user could have switched back from instant. restore settings
                days_bitfield = feed.last_custom_digest_days
            feed.digest_days = days_bitfield

        else:
            print "xxx"
            return
                        
        feed.save()

        # Update User and Feed for _digest_next datetime 
        updateUserNextDigest(user, getUserPrefs(user))
        
        self.redirect("/feeds/update/%s" % key)

class FeedDelete(webapp.RequestHandler):
    def post(self, key):
        user = users.get_current_user()

        feeds = db.GqlQuery("SELECT * FROM Feed WHERE __key__ = :1 AND user = :2", db.Key(key), user)
        feed = feeds.get() #fetch(1)[0]

        if self.request.get("cancel"):
            self.redirect("/feeds/update/%s" % feed.key())
            return 
            
        if self.request.get("delete"):
            feed.delete()
            self.redirect("/feeds")
            
        else:
            path = os.path.join(os.path.dirname(__file__), '%sfeeds_delete.html' % TEMPLATES_DIR)
            self.response.out.write(template.render(path, { 'user': user, 'feed': feed }))        

class Test(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        user_prefs = getUserPrefs(user)

        print "x"
        print user
        #print user_prefs

        x = updateUserNextDigest(user, user_prefs)
        print "now: ", datetime.datetime.now()
        print "next:", x
        print 
        print dir(user)
        print user.email()
        print
        