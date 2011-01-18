from google.appengine.ext import webapp
from django.template import Node 

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

class ResetCycleNode(Node): 
    def __init__(self, cyclenodes): 
        self.cyclenodes = cyclenodes 
    def render(self, context): 
        for c in self.cyclenodes.values(): 
            c.counter = -1 
        return '' 

@register.tag 
def resetcycle(parser, token): 
    # if you need tag error checking have a look at the Django 
    #defaulttag.py file on how to do it 
    return ResetCycleNode(getattr(parser,'_namedCycleNodes',{}))     