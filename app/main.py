#!/usr/bin/env python

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from modules.models import *
from modules.handlers import *

urls = [
    (r'/', MainPage),
    (r'/feeds', FeedsPage),
    (r'/feeds/update/([-\w]+)', FeedSettings),
    (r'/feeds/delete/(.*)', FeedDelete),
    (r'/signin', SignIn),
    (r'/signout', SignOut),
    (r'/help', Help),
    (r'/test', Test),
]

application = webapp.WSGIApplication(urls, debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()