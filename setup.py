from setuptools import setup, find_packages

setup(
    name='redfox',
    version='1.2',
    author='Owen Jacobson',
    author_email='owen.jacobson@grimoire.ca',
    
    url='http://code.google.com/p/python-redfox/',
    download_url='http://code.google.com/p/python-redfox/downloads/list',
    description='WSGI request routing for Python objects',
    long_description="""
Redfox provides a simple, declarative routing mechanism for creating
WSGI entry points into applications. It's broadly similar to
microframeworks like juno_ or CherryPy_.

.. _juno: http://github.com/breily/juno/tree/master
.. _CherryPy: http://www.cherrypy.org/

Features
--------

1. It's tiny. The ``redfox`` package contains under 100 lines of code.
   Redfox builds heavily on the Werkzeug tools to implement its features,
   rather than re-reinventing the wheel.
2. It's clean. The following is a valid Redfox application class::

    from werkzeug import Response
    from redfox import WebApplication
    from redfox.routing import get, post

    class Example(WebApplication):
        @get('/')
        def index(self, request):
            return Response("Hello, world!")

3. It's minimal. Redfox does not impose a persistance mechanism, or a
   view mechanism. Bring your own, or create your own tools.
""",
    
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Paste',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Internet :: WWW/HTTP :: WSGI',
        'Topic :: Software Development :: Libraries :: Application Frameworks'
    ],
    
    packages=find_packages(),
    
    install_requires=[
        'Werkzeug',
    ],
    
    entry_points = {
        'paste.app_factory': [
            'example=redfox.examples:Example',
            'inherited=redfox.examples:InheritanceExample',
            'redirecty=redfox.examples:RedirectyExample',
        ]
    },
)
