RSS-to-Email Webapp in Python for Google AppEngine.

Website: [http://www.feedserf.com] [1]

Users can manage feeds, select digest intervals and will receive emails
as soon as new items are available in the feed and the next digest interval
is reached.

License under the [GNU AGPL] [2]

  [1]: http://www.feedserf.com
  [2]: http://www.gnu.org/licenses/agpl.html 

Internals
=========

Feeds
-----
There is one Feed object per user. If multiple users subscribe to the same
RSS source, it is only crawled once and all user-feeds are updated.

Storing Digest Days
-------------------
Currently each Feed has custom digest settings. The backend is also able to
store multiple digest setting groups per user which can be applied to feeds.  

Digest days are stored in an integer attribute 'digest_days' as a bitfield:  
Mon=1, Tue=2, Wed=4, .., So=64. 0=Instant digest (send mail when new item is 
available).

With the bitfield we can check if the user receives an email on Tuesday like
this: if (digest_days & 2) 

Crawling Feeds
--------------
A cron job runs once every hour:

1. build a list of unique feeds to crawl (avoiding duplicates) and put them in 
   a queue so that every feed is fetched in parallel.
   
2. after crawling one feed, update all respective user-feeds, and if new item
   available for a user, update UserPrefs._items_ready.

Sending Emails
--------------
1.  A cron job runs every minute which gets a list of users that have new items
    and the _digest_next <= now (done in services.CheckSendMail):

    ``select * from UserPrefs where _digest_next <= now() and _items_ready = True``

    Put each user into a task-queue to update users in parallel
    
2.  For each user that has update, find feeds to check for sending mail now
    * get this user's feeds with new items and _digest_next <= now
    * for all items: copy into buffer and delete from db
    * After collecting all items, build email(s) and send
    * reset user's items ready
    * update next scheduled digest for user and all feeds

        