# Notice #

Redfox has moved to [GitHub](https://github.com/ojacobson/redfox). This Google Code site is effectively dead; in particular, if you want to suggest changes or request help, you're better off there than here.

# Welcome to Redfox #

Redfox provides a simple, declarative routing mechanism for creating WSGI entry points into applications. It's broadly similar to microframeworks like [juno](http://github.com/breily/juno/tree/master) or [CherryPy](http://www.cherrypy.org/).

## Features ##

  1. It's tiny. The `redfox` package contains under 100 lines of code. Redfox builds heavily on the [Werkzeug](http://werkzeug.pocoo.org/) tools to implement its features, rather than re-reinventing the wheel.
  1. It's clean. The following is a valid Redfox application class:
```
from werkzeug import Response
from redfox import WebApplication
from redfox import get, post

class Example(WebApplication):
    @get('/')
    def index(self, request):
        return Response("Hello, world!")
```
  1. It's minimal. Redfox does not impose an ORM model, or a templating system. Bring your own, or create your own tools.

See the GettingStarted guide for a step-by-step guide for creating a complete Redfox application.