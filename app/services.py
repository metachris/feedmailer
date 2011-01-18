#!/usr/bin/env python

"""
Services that are accessible to admin only (eg. cron).

- Each minute: check for users which should receive an email
- Each hour: crawl feeds and update users
"""

import datetime

from urllib2 import quote as url_quote
from urllib2 import unquote as url_unquote

from google.appengine.ext import webapp
from google.appengine.api import taskqueue
from google.appengine.ext.webapp.util import run_wsgi_app

from google.appengine.api import mail

from lib import feedparser

from modules.models import *
from modules.handlers import *
from modules.tools import *

TEMPLATES_DIR = "templates/"

class CheckSendMail(webapp.RequestHandler):
    def get(self):
        """Run by cron job every minute"""
        print "x"
        userprefs = db.GqlQuery("SELECT * FROM UserPrefs WHERE _digest_next <= :1 AND _items_ready = True", datetime.datetime.now())
        for prefs in userprefs:
            taskqueue.add(url='/services/sendmail_worker/%s' % prefs.key())
            print prefs, prefs.key(), "dispatched"

class SendMailWorker(webapp.RequestHandler):
    """Triggered by last minutes check. Items ready to be sent and _digest_next <= now.
    
    - Update _digest_next and _item_ready on UserPrefs
    - Compile Email
    - Send Email
    
    Args: key = UserPrefs key of this user
    """
    def post(self, key):
        return self.get(key)
    
    def get(self, key):
        user_prefs = UserPrefs.get(key)
        if not user_prefs:
            return

        # Find all feeds with email scheduled for now or past        
        _feeds = db.GqlQuery("SELECT * FROM Feed WHERE _digest_next <= :1 and user = :2", datetime.datetime.now(), user_prefs.user)
        feeds = []
        for feed in _feeds:
            if feed.feeditem_set.count() > 0:
                # this feed has items ready and scheduled to be sent now
                f = { 'feed': feed, 'items': [] }
                for item in feed.feeditem_set:
                    f["items"].append(item)
                    item.delete()
                feeds.append(f)

        print "x"
        print feeds
        
        # save that this users currently ready items are already handled        
        user_prefs._items_ready = False
        
        # update user's and feeds _digest_next. lte_now excludes now and
        # always sets _digest_next in the future. Also updates all feeds
        # _digest_next datetime (in the future, not now (lte_new=true))
        updateUserNextDigest(user_prefs.user, user_prefs, lte_now=True)
        
        print "feeds with items ready:", len(feeds)
        print "x"
        if len(feeds) > 0:
            # compile email now            
            template_values = { 'user': user_prefs.user, 'feeds': feeds, 'feed_cnt': len(feeds) }            

            path = os.path.join(os.path.dirname(__file__), '%semail_feedupdate_text.html' % TEMPLATES_DIR)
            email_body_text = template.render(path, template_values)        
            path = os.path.join(os.path.dirname(__file__), '%semail_feedupdate_html.html' % TEMPLATES_DIR)
            email_body_html = template.render(path, template_values)        
            print email_body_text
            
            # Increment email sent counter on feeds
            for _feed in feeds:
                #print _feed
                _feed["feed"].emails_sent += 1
                _feed["feed"].save()
                
            # compose subject line
            subject = "Feed digest of"
            for i in xrange(len(feeds)):
                if i < 2:
                    subject += " %s," % feeds[i]["feed"].title
                else:
                    subject += " and %s others" % (len(feeds) - 2)
                    break

            message = mail.EmailMessage()
            message.sender = "Feedserv Digest <digest@feedserf.com>"
            message.to = user_prefs.email
            message.subject = subject
            message.body = email_body_text
            message.html = email_body_html
            message.send()
            
            user_prefs.emails_received += 1
            user_prefs.emails_last = datetime.datetime.now()
            user_prefs.save()
            
class InitFeedCrawler(webapp.RequestHandler):
    def get(self):
        """Run by cron job every hour"""
        print "x"
        # 1. get unique feed list
        feeds = []
        feeds_keys = []
        feeds_all = db.GqlQuery("SELECT * FROM Feed")
        for feed in feeds_all:
            if not feed.link_rss in feeds:
                feeds.append(feed.link_rss)
                feeds_keys.append(feed.key())
            
        # 2. dispatch to crawlers
        for key in feeds_keys:
            taskqueue.add(url='/services/crawl_feed_worker/%s' % key)            
            print key, "dispatched"

class FeedCrawler(webapp.RequestHandler):
    """Reads an external feed and updates all User-Feeds with new items.
    
    Argument key is a reference Feed with a unique feed_url
    
    After crawling, all User-Feeds with that url are checked for new items,
    and if available, FeedItem objects are created which will be used by next
    scheduled sendmail check.
    """
    def post(self, key):
        return self.get(key)

    def get(self, key):
        print "x"
        _feed = Feed.get(key)
        if not _feed:
            return
                
        f = feedparser.parse(_feed.link_rss)    
        print "- status:", f.status
        if f.status != 200 or not f.feed.has_key("title"):
            # Error in parsing. Skip this and retry with next cron
            return 
        
        # f.updated is a time.struct_time(tm_year=2011, tm_mon=1, 
        #                  tm_mday=14, tm_hour=12, tm_min=16, 
        #                  tm_sec=43, tm_wday=4, tm_yday=14, tm_isdst=0)
        # 
        # convert into datetime object            
        # updated = datetime.datetime(*f.updated[:6])

        now = datetime.datetime.now()
                
        # Get a list of userfeeds that subscribe to the fetched feed, check for new items
        feeds = db.GqlQuery("SELECT * FROM Feed WHERE link_rss = :1", _feed.link_rss)
        for feed in feeds:
            print "- update feed:", feed
            feed.date_last_crawled = now
            
            # Traverse f.entries until we find one item in the feed's recent 
            # history. All items until then are new and added to the queue.
            for i in xrange(len(f.entries)):
                if f.entries[i].link in feed._recent_items:
                    break
            
            # i now contains the number of leading entries that are unknown to this user
            print "--", i, "new items"

            if i == 0:
                feed.save() # for feed.date_last_crawled
                return
                
            for j in xrange(i):
                # add oldest items first, newest last (instead of starting 0..3,
                # we revert the sequence and start from 3 .. 0)
                pos = i - j - 1
 
                item = FeedItem(feed=feed, user=feed.user, title=f.entries[pos].title, link=f.entries[pos].link)
                item.save()

                print "created:", item
                
                # Add to _recent_items and truncate if necessary
                feed._recent_items.append(item.link)
                print item.link
                if len(feed._recent_items) > 10:
                    feed._recent_items.pop(0)
         
                # print "recent items:", feed._recent_items
 
            # _recent_items have been added. save.               
            feed.save()

            # print "x"
            
            # there have been items added to this users queue. save.
            prefs = getUserPrefs(feed.user)
            prefs._items_ready = True
            prefs.save()
            
urls = [
    (r'/services/check_sendmail', CheckSendMail),
    (r'/services/sendmail_worker/([-\w]+)', SendMailWorker),

    (r'/services/crawl_feeds', InitFeedCrawler),
    (r'/services/crawl_feed_worker/([-\w]+)', FeedCrawler),
]

application = webapp.WSGIApplication(urls, debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()