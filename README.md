Crawling Feeds
-------------- 

A cron job runs once every hour.

1. build a list of feeds to crawl (avoiding duplicates)

    feed_urls = getUniqueFeedLinks()
    
2. crawl feeds in parallel

    f = feedparser.parse(feed_url)
    
    # get all userfeed entries for the fetched feed
    select * from Feed where link_rss = feed_url
    
    # add new items to every user-feeds and set UserPref 
    foreach feed:
        feed.addNewItems(f.items)
        UserPrefs._items_ready = True

Sending Emails
--------------

1.  A cron job runs every minute which gets a list of users that get a mail

    select * from UserPrefs where _digest_next <= now() and _items_ready

2.  For each user that has update, find feeds to update

    # reset items ready
    user.userprefs_set._items_ready = False 
    
    # update next scheduled date
    user.userprefs_set._digest_next = ... 
    
    # get feeds with new items
    select * from Feed where user = user and (digest_days == 0 or _digest_next <= now())
        and feed.feeditem_set.count() > 0

    # for all items: copy into buffer and delete from db

    # After collecting all items, build email(s) and send

        