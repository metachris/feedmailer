#!/usr/bin/env python

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from modules.models import *
from modules.handlers import *

urls = [
    ('/', MainPage),
    ('/feeds', FeedsPage),
    (r'/feeds/update/(.*)', FeedSettings),
    (r'/feeds/delete/(.*)', FeedDelete),
    ('/test', Test),
]

application = webapp.WSGIApplication(urls, debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()