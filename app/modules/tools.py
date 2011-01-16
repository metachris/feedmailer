import datetime

def calcNextDigestDateTime(digest_days, digest_time):
    """Find soonest date in the future matching the days_bitfield and time"""
    if digest_days == 0:
        # instant digest
        return datetime.datetime.now()
    
    # Extract bitfield and find closest update date from now
    weekday = datetime.datetime.now().weekday() # Mon=0, Sun=6
    time_now = datetime.datetime.now().time()
    for i in xrange(8):
        day = (i + weekday) % 7
        if digest_days & 1<<day:
            # is soonest date, if not earlier today
            if i == 0 and digest_time < time_now:
                continue
            else:
                # soonest date found. end traversing                
                break
    
    d = datetime.datetime.now() + datetime.timedelta(days=i)
    next_date = datetime.datetime(d.year, d.month, d.day, digest_time.hour, digest_time.minute)
    print "next update: %s days from now (weekday=%s)" % (i, day)
    print next_date         
    return next_date
    
def getUserNextDigestDateTime(user):
    feeds = db.GqlQuery("SELECT * FROM Feed WHERE user = :1", user)
    
    # Traverse all Feeds and find soonest date in the future
    next_min = None
    for feed in feeds:
        next_tmp = calcNextDigestDateTime(feed.digest_days, feed.digest_time)
        if next_tmp < next_min:
            next_min = next_tmp