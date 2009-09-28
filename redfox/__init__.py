"""Redfox provides a simple, declarative routing mechanism for creating
WSGI entry points into applications. It's broadly similar to
microframeworks like juno_ or CherryPy_.
"""

import redfox.meta
from redfox.routing import route, get, post, put, delete

__all__ = [
    'WebApplication',
    'route',
    'get',
    'post',
    'delete',
    'rule_map'
]

class WebApplication(object):
    """Web application classes should extend this class, rather than
    using the ``redfox.meta.WebApplication`` metaclass. The following
    example is a Hello World application::
    
        from redfox import WebApplication, get
        from werkzeug import Response
        
        class Example(WebApplication):
            @get('/')
            def index(self, request):
                return Response('Hello, world!')
    
    """
    __metaclass__ = redfox.meta.WebApplication

rule_map = redfox.meta.WebApplication.rule_map
