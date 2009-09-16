from werkzeug import Response
from werkzeug.routing import Rule
from redfox import WebApplication
from redfox import get, post, rule_map

class Example(WebApplication):
    def __init__(self, global_config, message, **config):
        self.message = message
    
    @get('/')
    @get('/index.html')
    def index(self, request):
        return Response(request.build(
            'echo_qs',
            dict(message=self.message),
            force_external=True
        ))
    
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

    rules = property(rule_map)

    def __init__(self, global_config, **config):
        pass

    @get('/')
    def index(self, request):
        return Response(repr([rule for rule in self.rules.iter_rules()]))
