#!/usr/bin/env python

"""
Cron job runs every minute to see if any user needs a mail.
"""

import datetime

from urllib2 import quote as url_quote
from urllib2 import unquote as url_unquote

from google.appengine.ext import webapp
from google.appengine.api import taskqueue
from google.appengine.ext.webapp.util import run_wsgi_app

from modules.models import *
from modules.handlers import *

from lib import feedparser

class CheckSendMail(webapp.RequestHandler):
    def get(self):
        """Run by cron job every minute"""
        users = db.GqlQuery("SELECT * FROM UserPrefs WHERE _digest_next <= :1 AND _items_ready = false", datetime.datetime.now())
        for user in users:
            print user        

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
            #taskqueue.add(url='/services/crawl_feed_worker/%s' % key)            
            print key, "dispatched"

class FeedCrawler(webapp.RequestHandler):
    """Reads an external feed and updates all User-Feeds with new items.
    
    Argument key is a reference Feed with a unique feed_url
    
    After crawling, all User-Feeds with that url are checked for new items,
    and if available, FeedItem objects are created which will be used by next
    scheduled sendmail check.
    """
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
        updated = datetime.datetime(*f.updated[:6])
        
        # Get a list of userfeeds that subscribe to the fetched feed, check for new items
        feeds = db.GqlQuery("SELECT * FROM Feed WHERE link_rss = :1", _feed.link_rss)
        for feed in feeds:
            print "- update feed:", feed

            # Traverse f.entries until we find something in the history. Then add to queue
            for i in xrange(len(f.entries)):
                if f.entries[i].link in feed._recent_items:
                    break
            
            # i now contains the number of leading entries that are unknown to this user
            print "--", i, "new items"
            for j in xrange(i):
                # instead of starting 0..3 we revert the sequence and start from 3 .. 0
                pos = i - j - 1
 
                item = FeedItem(feed=feed, user=feed.user, title=f.entries[pos].title, link=f.entries[pos].link)
                item.save()

                print "created:", item
                
                # Add to _recent_items and truncate if necessary
                feed._recent_items.append(item.link)
                if len(feed._recent_items) > 10:
                    feed._recent_items.pop(0)
                feed.save()
                    
                print "recent items:", feed.__recent_items
                
urls = [
    ('/services/check_sendmail', CheckSendMail),
    ('/services/crawl_feeds', InitFeedCrawler),
    (r'/services/crawl_feed_worker/([-\w]+)', FeedCrawler),
]

application = webapp.WSGIApplication(urls, debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()