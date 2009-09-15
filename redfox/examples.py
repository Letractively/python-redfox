from werkzeug import Response
from werkzeug.routing import Rule
from redfox import WebApplication
from redfox import get, post

class Example(WebApplication):
    def __init__(self, global_config, message, **config):
        self.message = message
    
    @get('/')
    @get('/index.html')
    def index(self, request):
        return Response(self.message)
    
    @get('/echo/<message>')
    def echo_qs(self, request, message):
        return Response(message)

class InheritanceExample(Example):
    @post('/')
    def post_index(self, request):
        return Response("I've totally hidden my parent class's behaviour.")
    
    def index(self, request):
        return Response("Derived class, k thx.")
    
    @get('/ok')
    def ok(self, request):
        return Response('Ok.')

class RedirectyExample(WebApplication):
    __rules__ = [
        Rule('/index', redirect_to='.')
    ]

    def __init__(self, global_config, message, **config):
        self.message = message

    @get('/')
    def index(self, request):
        return Response(self.message)
