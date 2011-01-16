import datetime

from google.appengine.ext import db
from google.appengine.api import users

def calcNextDigestDateTime(digest_days, digest_time, lte_now=False):
    """Find soonest date in the future matching the days_bitfield and time
    
    If lte_new = True, exclude _digest_next that would be now. instead use
    next one in the future. (used when updating next feed schedule on sending 
    email, which would be set to now.
    """
    if digest_days == 0:
        # instant digest
        return datetime.datetime.now()
    
    # Extract bitfield and find closest update date from now
    now = datetime.datetime.now()
    weekday = now.weekday() # Mon=0, Sun=6
    time_now = now.time()
    for i in xrange(8):
        day = (i + weekday) % 7
        if digest_days & 1<<day:
            # is soonest date, if not earlier today
            if i == 0:
                # if today, make sure it's not already past (or now if lte_new)
                if (not lte_now and digest_time < time_now) or \
                   (lte_now and digest_time <= time_now):
                    continue
            else:
                # soonest date found. end traversing                
                break
    
    d = now + datetime.timedelta(days=i)
    next_date = datetime.datetime(d.year, d.month, d.day, digest_time.hour, digest_time.minute)
    #print "next update: %s days from now (weekday=%s)" % (i, day)
    #print next_date         
    return next_date
    
def getUserNextDigestDateTime(user, updateFeedDigestNext=False, lte_now=False):
    """Returns the users soonest next email check as datetime object
    
    if updateFeedDigestNext is set to True, all feeds will update and save 
    their next scheduled digest_next datetime object
    """
    feeds = db.GqlQuery("SELECT * FROM Feed WHERE user = :1", user)
    
    # Traverse all Feeds and find soonest date in the future
    next_min = None
    for feed in feeds:
        next_tmp = calcNextDigestDateTime(feed.digest_days, feed.digest_time, lte_now)
        if not next_min or next_tmp < next_min:
            next_min = next_tmp
        if updateFeedDigestNext:
            feed._digest_next = next_tmp
            feed.save()
    
    return next_min
    
def updateUserNextDigest(user, prefs, lte_now=False):
    """Updates _digest_next on user and on all its feeds. Triggered at:
    - adding feed
    - feed custom interval update
    - global interval settings update (not yet impl.)
    - triggered next scheduled digest
    
    if lte_now is True, feeds with new _digest_next == now (this minute)
    will get the _digest_next set to the next in the future. if False
    _digest_next will be set to now if now.
    """
    next = getUserNextDigestDateTime(user, True, lte_now) # True = update all Feeds for next schedule
    prefs._digest_next = next
    prefs.save()
    
    return next