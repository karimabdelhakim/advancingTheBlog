from urllib import quote_plus 
from django import template

register = template.Library()

@register.filter
def urlify(value):
	return quote_plus(value)

"""
this is a custom filter for any template (i am using it for post_detail.html)
this filter url-encode text or a content of a post as i did in post_detial.html
example:  hi my name is karim >> hi+my+name%20is%20karim 
"""