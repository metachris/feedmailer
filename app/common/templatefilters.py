# import the webapp module
from google.appengine.ext import webapp

# get registry, we need it to register our filter later.
register = webapp.template.create_template_register()

def days_bitfield_humanize(days_bitfield):
    """Converts a days_bitfield into a human readable string (Mon, Tue, ...)"""
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    o = ""
    for i in xrange(7):
        if days_bitfield & 1<<i:
            o += " %s," % days[i]
    return o.strip().strip(",")
    
register.filter(days_bitfield_humanize)
    