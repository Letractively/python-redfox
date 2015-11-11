# Introduction #

Let's build a simple "pastebin" application (like http://paste.pocoo.org/) to illustrate how Redfox works with tools like templating libraries, ORMs, and deployment tools. For this example, we'll be using the following tools:

  * [Redfox](http://code.google.com/p/python-redfox/) to route URLs to our application.
  * Parts of [Werkzeug](http://werkzeug.pocoo.org/) for handling static content and request data.
  * [Paste](http://pythonpaste.org/) to configure and run the application.
  * [Mako](http://www.makotemplates.org/) for our templates.
  * [Pygments](http://pygments.org/) for syntax highlighting.
  * [SQLAlchemy](http://www.sqlalchemy.org/) to store and retrieve pastes.

We'll also be using a few supporting tools to handle our workspace:

  * [Setuptools](http://peak.telecommunity.com/DevCenter/setuptools) to tell Paste how to find our application and to manage dependencies.
  * [Virtualenv](http://pypi.python.org/pypi/virtualenv) to give us a clean workspace.

# Setup #

Before we get started, we'll need an environment to work in. This isn't strictly necessary, but virtualenv will let us install Python packages and libraries without interfering with the system-wide Python installation. (If you already know your way around `virtualenv`, `easy_install`, and friends, you can skip straight to the last command in this section.) If you don't have it already, install the `virtualenv` package. If you're on a Debian- or Ubuntu-based system, you can install it using `sudo apt-get install python-virtualenv`. Otherwise, download the [source package](http://pypi.python.org/pypi/virtualenv) and unpack it. Let's call our environment `red`:

```
$ virtualenv ~/red
```

(If you downloaded the virtualenv source package, you'll need to run the `virtualenv.py` script, instead.)

Once virtualenv finishes creating the environment, you'll need to "activate" it so that the `python` and `easy_install` commands know to work with the virtual environment. Virtualenv creates a script to do this, which you can source in your shell:

```
source ~/red/bin/activate
```

You should see `(red)` before your prompt when the virual environment is active. You can verify that it's set up by typing `which easy_install` - you should see something similar to `/home/owen/red/bin/python`. If you see `/usr/bin/python` or any other system-wide path, check the output of the commands you've run to see what went wrong.

We'll install Paste in the new environment, using `easy_install`, because Paste isn't part of the application proper. Let's do that now:

```
(red)$ easy_install PasteScript PasteDeploy
```

These packages provide the `paster` command, which we'll be using to run our application.

# Hello, World! #

We'll start with an empty setuptools-based project. Create the project dir and an empty package:

```
$ mkdir ~/red/paste
$ cd ~/red/paste
$ mkdir redpaste
$ touch redpaste/__init__.py
```

Create `setup.py`:

```
from setuptools import setup, find_packages

setup(
    name='redpaste',
    version='0.dev',
    
    packages=find_packages(),
    include_package_data=True,

    install_requires=[
        'Werkzeug',
        'redfox',
        'sqlalchemy',
        'mako',
        'Pygments',
        'setuptools'
    ]
)
```

And, finally, install all the dependencies:

```
$ python setup.py develop
```

Of course, an empty project doesn't really do much. Create `redpaste/app.py`:

```
from werkzeug import Response
from redfox import WebApplication, get, post

class Pastebin(WebApplication):
    def __init__(self, global_config=None, **local_config):
        # Paster app_factory entry point. The configuration entries from
        # the application config file will be passed in via local_config
        # and global_config.
        #
        # For now, though, we do nothing.
        pass
    
    @get('/')
    def index(self, request):
        return Response('Hello, world!')
```

We'll also need to tell `setuptools` to expose our application to Paste. Add an `entry_points` argument to `setup.py`:

```
from setuptools import setup, find_packages

setup(
    name='redpaste',
    version='0.dev',
    
    packages=find_packages(),
    
    install_requires=[
        'Werkzeug',
        'redfox',
        'sqlalchemy',
        'mako',
        'Pygments',
        'setuptools'
    ],

    entry_points = {
        'paste.app_factory': [
            'pastebin=redpaste.app:Pastebin'
        ]
    }
)
```

Since we changed `setup.py`, we'll also need to re-run `python setup.py develop`.

The `paste.app_factory` entry point type is [used by Paste](http://pythonpaste.org/deploy/#paste-app-factory) to figure out what objects correspond to web application components. Paste also needs a configuration file. Let's call ours `redpaste.ini`:

```
[app:main]
# Tell Paste to serve our application as the main app.
use = egg:redpaste#pastebin

[server:main]
# Let Paste host the application itself, for development.
use = egg:Paste#http
port = 9999
```

Our application is ready to start. Start Paste:

```
$ paster serve redpaste.ini
```

Then visit your application at http://localhost:9999/ and say "hi."

# Storing Pastes #

Our pastebin application is going to need to store submitted pastes for display later. Using [SQLAlchemy](http://www.sqlalchemy.org/), this is fairly straightforward. We'll also use Sqlite3, which is built-in in recent versions of Python, to store data.

Create `redpaste/storage.py`, and let's define our model:

```
from random import sample, randrange
from datetime import datetime
from sqlalchemy import Column, Unicode, UnicodeText, DateTime
from sqlalchemy.ext.declarative import declarative_base

ID_CHARS = u'abcdefghijkmpqrstuvwxyzABCDEFGHIJKLMNPQRST23456789'
ID_SIZE = 12

def generate_id():
    return ''.join(sample(ID_CHARS, ID_SIZE))

Mapped = declarative_base()

class Paste(Mapped):
    __tablename__ = 'paste'
    
    def __init__(self, author, body, syntax):
        self.author = author
        self.body = body
        self.syntax = syntax
    
    # A generated ID for each paste.
    id = Column(Unicode(ID_SIZE), primary_key=True, default=generate_id)
    # The paste's author.
    author = Column(Unicode, nullable=False)
    # The actual pasted text.
    body = Column(UnicodeText, nullable=False)
    # The paste's language, for syntax highlighting.
    syntax = Column(Unicode, nullable=False)
    # The time at which the paste was created.
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
```

We're using SQLAlchemy's declarative mapping extension to define a table and a class that maps to it all at once. Since this is a brand-new app and [it's not 1980 any more](http://www.joelonsoftware.com/articles/Unicode.html), we've assumed unicode column types up front.

It's not strictly necessary, but our application will be a bit cleaner if we define a data access layer to translate between application-level requests ("get paste 51") and SQLAlchemy queries ("SELECT **FROM paste WHERE id = '51'"). Add it to `storage.py`:**

```
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
# ...
class PasteStore(object):
    def __init__(self, url):
        self.engine = create_engine(url)
        Mapped.metadata.create_all(self.engine)
        
        self.Session = sessionmaker(
            bind=self.engine,
            expire_on_commit=False
        )
    
    def latest(self, count=10):
        """Retrieves the last ``count`` pastes."""
        session = self.Session()
        try:
            return session.query(Paste).order_by(Paste.timestamp.desc())[0:count]
        finally:
            session.close()
    
    def get(self, id):
        """Retrieves a specific paste."""
        session = self.Session()
        try:
            return session.query(Paste).filter(Paste.id==id).one()
        except NoResultFound:
            raise KeyError, id
        finally:
            session.close()
    
    def new(self, author, body, syntax):
        """Creates and returns a new paste."""
        paste = Paste(author, body, syntax)
        session = self.Session()
        try:
            session.add(paste)
            paste = session.merge(paste)
            session.commit()
            return paste
        finally:
            session.close()
```

Our `PasteStore` also creates our schema for us, using the schema described by the `Paste` class.

Our application will use a `PasteStore` to create and find `Paste`s. We just have to tell our application where to store the database. We'll do this through `redpaste.ini`, by adding a new field to the `[app:main]` section:

```
[app:main]
# Tell Paste to serve our application as the main app.
use = egg:redpaste#pastebin
# The SQLAlchemy database URL pointing to our pastebin's storage.
database_url = sqlite:///redpaste.db
```

The database will be stored on disk, allowing pastes to survive across restarts. We could also use `sqlite:///:memory:` to use a purely in-memory database, which would be lost every time the application shuts down.

Our application needs to know what to do with this parameter, so let's modify `Pastebin`'s constructor, in `redpaste/app.py`:

```
from redpaste.storage import PasteStore
# ...
class Pastebin(WebApplication):
    def __init__(self, global_config, database_url, **local_config):
        # Paster app_factory entry point. The configuration entries from
        # the application config file will be passed in via local_config,
        # keyword parameters, and global_config.
        self.paste_store = PasteStore(database_url)
    # ...
```

Now, if we start our application again, we should see `redpaste.db` created. We can open it with `sqlite3 redpaste.db`:

```
$ sqlite3 redpaste.db 
SQLite version 3.6.12
Enter ".help" for instructions
Enter SQL statements terminated with a ";"
sqlite> .schema
CREATE TABLE paste (
	id VARCHAR(12) NOT NULL, 
	author VARCHAR NOT NULL, 
	body TEXT NOT NULL, 
	syntax VARCHAR NOT NULL, 
	timestamp TIMESTAMP NOT NULL, 
	PRIMARY KEY (id)
);
```

Well, that definitely looks like the schema we defined. If we make changes to the schema in `redpaste/storage.py`, we'll need to delete `redpaste.db` or make the same changes to it using `ALTER TABLE` statements.

# Shark Food #

Our application reacts to requests, and it's starting to know how to store pastes, but we're going to need a way to display things. While we could build up the entire response in Python, it's easier to use a template language. We've chosen [Mako](http://www.makotemplates.org/), which is fairly easy to work with.

When our application tells Mako to render a template, it passes keyword arguments to `template.render` containing any extra data. We'll adopt the convention that methods that will be used with templates return `dict` objects containing the arguments to pass, and write a short [decorator](http://www.python.org/dev/peps/pep-0318/) that associates a template with a method. We'll start with our `index` method:

```
class Pastebin(WebApplication):
    # ...
    @get('/')
    @template('index.mako')
    def index(self, request):
        return dict(
            latest=self.paste_store.latest()
        )
```

Our template will use the `latest` parameter to show a sidebar listing the last few pastes.

We'll also need to define the `template` decorator. Because Python processes modules from the top down, and because the decorator has to be available when Python parses the class body, this has to go _above_ `class Pastebin(WebApplication):`

```
from functools import wraps
from pkg_resources import resource_filename
from mako.template import Template
from mako.lookup import TemplateLookup

# Mako uses TemplateLookup objects to handle references between
# templates.
template_lookup = TemplateLookup(directories=[
    # Look in our distribution, in the ``redpaste/templates/`` directory.
    resource_filename(__name__, 'templates')
])

def template(name):
    """Returns a decorator that replaces the return value of a function.
    The decorated function is expected to return a dict, which is converted
    into keyword arguments for Mako. The resulting, rendered template is
    wrapped up in a Response."""
    def template_decorator(f):
        @wraps(f)
        def template_responder(self, request, *args, **kwargs):
            response = f(self, request, *args, **kwargs)
            template = template_lookup.get_template(name)
            body = template.render(**dict(
                request=request,
                **response
            ))
            return Response(body, mimetype='text/html')
        return template_responder
    return template_decorator
```

It's a little ugly, but it works. We pass the request along to the template in case we need to build URLs -- more on that in a while.

We'll also need a template. In the template\_lookup definition above, we've told Mako to look in `redpaste/templates` for templates, so create that directory and create `index.mako` in it:

```
<%page args='latest'/>
<html>
<head>
    <title>Redpaste</title>
</head>
<body>
    <h1>Redpaste</h1>

    ${list_latest(latest)}
    ${new()}
    ${footer()}
</body>
</html>

<%def name="list_latest(pastes)">
<div id="latest">
    <h2>Recent Pastes</h2>
    <ul>
        % for paste in pastes:
            <li><a href="${paste.id |u}">${paste.author |h}</a><br>
                ${format_datetime(paste.timestamp) |h}</li>
        % endfor
    </ul>
</div>
</%def>

<%def name="new(author='Anonymous Coward')">
<div id="new">
    <form action="." method="post">
        <fieldset>
            <legend>New Paste</legend>
            <table>
                <tr>
                    <th><label for="author">Your Name</label></th>
                    <td><input id="author" name="author" value='${author |h}'></td>
                </tr>
                <tr>
                    <th><label for="syntax">Language</label></th>
                    <td>
                        <select id="syntax" name="syntax">
                            <option select="selected" value="text">Plain Text</option>
                            <option value="python">Python 2.x</option>
                            <option value="python3">Python 3.x</option>
                            <option value="perl">Perl</option>
                            <option value="ruby">Ruby</option>
                            <option value="c">C</option>
                            <option value="cpp">C++</option>
                            <option value="java">Java</option>
                            <option value="objective-c">Objective-C</option>
                            <option value="scala">Scala</option>
                            <option value="csharp">C#</option>
                            <option value="common-lisp">Common Lisp</option>
                            <option value="erlang">Erlang</option>
                            <option value="haskell">Haskell</option>
                            <option value="ocaml">OCaml</option>
                            <option value="brainfuck">BrainFuck</option>
                            <option value="sql">SQL</option>
                        </select>
                    </td>
                </tr>
                <tr>
                    <td colspan="2">
                        <textarea cols="80" rows="15" name="body"></textarea>
                    </td>
                </tr>
            </table>
            <input type="submit" value="Paste it!">
        </fieldset>
    </form>
</div>
</%def>

<%def name="footer()">
    <address>Redpaste is powered by
        <a href="http://pythonpaste.org/">Paster</a>,
        <a href="http://werkzeug.pocoo.org/">Werkzeug</a>,
        <a href="http://www.sqlalchemy.org/">SQLAlchemy</a>,
        <a href="http://www.makotemplates.org/">Mako</a>,
        <a href="http://pygments.org/">Pygments</a>,
        <a href="http://code.google.com/p/python-redfox/">Redfox</a>,
        and, of course, <a href="http://www.python.org">Python</a>.
        Use Redpaste for <strong>awesome</strong>.</address>
</%def>

<%def name="format_datetime(datetime)">
    ${datetime.strftime("%b %d %I:%M:%S %p")}
</%def>
```

That giant list of languages is a tiny subset of Pygments' <a href='http://pygments.org/docs/lexers/'>supported languages list</a>. Feel free to tweak the list to your own tastes.

Now, let's restart `paster serve redpaste.ini` and visit http://localhost:9999/ again. If it all fit together right, we should see our template. Because the `redpaste.db` database is empty, there won't be any pastes listed under "Recent Pastes", but if you feel like it you can insert some data by hand using `sqlite3`.

# Remember Me Fondly #

If we try submitting a paste in our fancy new template-driven user interface, we'll notice a big problem: it doesn't work! Instead, we get an ugly "Method Not Allowed" error trying to post to `/`. Let's fix that by creating a handler that saves new pastes in `redpaste/app.py`'s `Pastebin` class:

```
from werkzeug import redirect
# ...
class Pastebin(WebApplication):
    # ...
    
    @post('/')
    def new_paste(self, request):
        author = request.form['author']
        body = request.form['body']
        syntax = request.form['syntax']
        
        paste = self.paste_store.new(author, body, syntax)
        return redirect(
            request.build_url(
                'paste',
                values=dict(id=paste.id),
                method='GET'
            ),
            code=SEE_OTHER
        )
```

We very carefully _don't_ render the resulting paste during the post. By redirecting with status 303 (See Other), we tell the browser to go `GET` the paste, which means the user can copy the URL straight out of their address bar. It also means we don't have to worry about duplicate `POST`s if the browser refreshes or the user navigates back.

Of course, this is only half the picture. We need to map the URL we just redirected the browser to to a page with their paste on it. Let's define one:

```
from werkzeug.exceptions import NotFound
# ...
class Pastebin(WebApplication):
    # ...
    @get('/<id>')
    @template('paste.mako')
    def paste(self, request, id):
        try:
            return dict(
                latest=self.paste_store.latest(),
                paste=self.paste_store.get(id)
            )
        except KeyError:
            raise NotFound
```

This endpoint is a little different from the ones we've defined so far: it has a parameter mapping in it. These handled by Redfox and Werkzeug and converted into method parameters for us. Our endpoint takes the ID out of the URL and attempts to display the corresponding paste. If there's no paste to be found, we raise `NotFound`, which gives back a `404` HTTP response to the browser.

We use `request.build_url`, which is provided as a thin wrapper over the Werkzeug `MapAdapter`'s `build` method, to assemble the URL, rather than hard-coding the URL: this allows Werkzeug to correctly build URLs in most deployment environments without hardcoded knowledge of the URL structure outside your application.

We'll also need to create a `paste.mako` template in `redpaste/templates`:

```
<%page args='latest, paste'/>
<%namespace name="layout" file="index.mako"/>
<html>
<head>
    <title>Redpaste - ${paste_title(paste)}</title>
</head>
<body>
    <h1>Redpaste - ${paste_title(paste)}</h1>
    
    ${layout.list_latest(latest)}
    
    <div id="paste">
        <h2>Pasted at ${layout.format_datetime(paste.timestamp) |h} by ${paste.author |h}</h2>
        <pre>${paste.body |h}</pre>
    </div>

    ${layout.new(author=paste.author)}
    ${layout.footer()}
</body>
</html>

<%def name="paste_title(paste)">
    ${paste.id |h} (${paste.syntax |h})
</%def>
```

If we restart `paster serve redpaste.ini` now, we should be able to go through the entire workflow from http://localhost:9999/ of creating a new paste and viewing it.

## Sidebar: Refactoring Templates ##

We've taken a shortcut in our templates that would eventually come back to bite us in a real-world application. Rather than importing functions from a template that's also used as a page in its own right, we can take advantage of Mako's template inheritance to define a common layout for our site. Start with a `layout.mako` file that defines the common parts of the layout:

```
<html>
<head>
    <title>${self.page_title()}</title>
</head>
<body>
    <h1>${self.page_title()}</h1>

    ${list_latest(latest)}
    ${next.body()}
    ${new()}
    ${footer()}
</body>
</html>

<%def name="page_title()">
    Redpaste
</%def>

<%def name="list_latest(pastes)">
<div id="latest">
    <h2>Recent Pastes</h2>
    <ul>
        % for paste in pastes:
            <li><a href="${request.build_url('paste', dict(id=paste.id))}">${paste.author |h}</a><br>
                ${format_datetime(paste.timestamp) |h}</li>
        % endfor
    </ul>
</div>
</%def>

<%def name="new(author='Anonymous Coward')">
<div id="new">
    <form action="${request.build_url('new_paste', method='POST')}" method="post">
        <fieldset>
            <legend>New Paste</legend>
            <table>
                <tr>
                    <th><label for="author">Your Name</label></th>
                    <td><input id="author" name="author" value='${author |h}'></td>
                </tr>
                <tr>
                    <th><label for="syntax">Language</label></th>
                    <td>
                        <select id="syntax" name="syntax">
                            <option select="selected" value="text">Plain Text</option>
                            <option value="python">Python 2.x</option>
                            <option value="python3">Python 3.x</option>
                            <option value="perl">Perl</option>
                            <option value="ruby">Ruby</option>
                            <option value="c">C</option>
                            <option value="cpp">C++</option>
                            <option value="java">Java</option>
                            <option value="objective-c">Objective-C</option>
                            <option value="scala">Scala</option>
                            <option value="csharp">C#</option>
                            <option value="common-lisp">Common Lisp</option>
                            <option value="erlang">Erlang</option>
                            <option value="haskell">Haskell</option>
                            <option value="ocaml">OCaml</option>
                            <option value="brainfuck">BrainFuck</option>
                            <option value="sql">SQL</option>
                        </select>
                    </td>
                </tr>
                <tr>
                    <td colspan="2">
                        <textarea cols="80" rows="15" name="body"></textarea>
                    </td>
                </tr>
            </table>
            <input type="submit" value="Paste it!">
        </fieldset>
    </form>
</div>
</%def>

<%def name="footer()">
    <address>Redpaste is powered by
        <a href="http://pythonpaste.org/">Paster</a>,
        <a href="http://werkzeug.pocoo.org/">Werkzeug</a>,
        <a href="http://www.sqlalchemy.org/">SQLAlchemy</a>,
        <a href="http://www.makotemplates.org/">Mako</a>,
        <a href="http://pygments.org/">Pygments</a>,
        <a href="http://code.google.com/p/python-redfox/">Redfox</a>,
        and, of course, <a href="http://www.python.org">Python</a>.
        Use Redpaste for <strong>awesome</strong>.</address>
</%def>

<%def name="format_datetime(datetime)">
    ${datetime.strftime("%b %d %I:%M:%S %p")}
</%def>
```

This is similar to our existing `index.mako`, but it has two interesting changes. First, we've replaced the string-interpolation-based URL construction with calls to `request.build_url`, which both reduces duplication, since only one place has to know the specifics of the URL structure, and handles most of the edge cases of URL parameter encoding correctly. Second, we've added a new template element: `${next.body()}` renders the contents of any template that inherits from `layout.mako`, giving us a spot to insert new body content. Now we can refactor `index.mako`:

```
<%inherit file="layout.mako"/>
```

The index page doesn't actually add anything to the template, so we don't define any body content. We can also refactor `paste.mako`:

```
<%inherit file="layout.mako"/>
<div id="paste">
    <h2>Pasted at ${self.format_datetime(paste.timestamp) |h} 
        by ${paste.author |h}</h2>
    <pre>${paste.body |h}</pre>
</div>

<%def name="page_title()">
    Redpaste - ${paste.id |h} (${paste.syntax |h})
</%def>
```

The body content here will be inserted between the list of recent pastes and the "new paste" form, exactly at the spot where our layout template has `${next.body()}`.

See the [inheritance](http://www.makotemplates.org/docs/inheritance.html) section in the Mako documentation for details on how Mako handles template inheritance.

# Syntax Highlighting #

At last, we have a working pastebin application. However, rendering pastes with `<pre>` is a bit plain. Pasted code is hard to read without some kind of syntax highlighting. Fortunately, [Pygments](http://pygments.org/) has a vast suite of syntax highlighters designed for this sort of use. We'll need to define a [Mako namespace](http://www.makotemplates.org/docs/namespaces.html) that exposes Pygments for our templates. Create `redpaste/highlight.py`:

```
import pygments
from pygments.lexers import get_lexer_by_name
from pygments.formatters import get_formatter_by_name
from pygments.styles import get_style_by_name

def highlight(context, body, syntax, format='html'):
    """Looks up the appropriate Pygments lexer for a given syntax
    and uses it to format the passed body.
    """
    lexer = get_lexer_by_name(syntax)
    formatter = get_formatter_by_name(format)
    
    return pygments.highlight(body, lexer, formatter)

def css_stylesheet(name, format='html'):
    """Returns the CSS associated with a Pygments Style."""
    formatter = get_formatter_by_name(format, style=name)
    
    return formatter.get_style_defs()
```

We'll also need to modify `redpaste/templates/paste.mako` to include our new namespace:

```
<%inherit file="layout.mako"/>
<%namespace name="syntax" module="redpaste.highlight"/>
<div id="paste">
    <h2>Pasted at ${self.format_datetime(paste.timestamp) |h} 
        by ${paste.author |h}</h2>
    ${syntax.highlight(paste.body, paste.syntax)}
</div>

<%def name="page_title()">
    ${paste.id |h} (${paste.syntax |h})
</%def>
```

If we restart `paster serve redpaste.ini`, we can see the syntax highlighting markup in the HTML source for paste entries (try it with a Python paste, for example). However, without stylesheets, there's no highlighting. Let's expose the CSS stylesheet Pygments generates for us. Add a new endpoint to the `Pastebin` application:

```
from redpaste.highlight import css_stylesheet
from pygments.util import ClassNotFound
# ...
class Pastebin(WebApplication):
    # ...
    @get('/styles/syntax/<name>')
    def syntax_styles(self, request, name):
        try:
            return Response(
                css_stylesheet(name),
                mimetype='text/css'
            )
        except ClassNotFound:
            raise NotFound
```

We also need to reference the stylesheet in our templates. Add it to `redpaste/templates/layout.mako`'s `<head>` section:

```
<head>
    <title>${self.page_title()}</title>
    <link rel="stylesheet" type="text/css" href="styles/syntax/default">
</head>
```

Now when we restart `paster serve redpaste.ini`, our pastes are nicely coloured!

# Fit and Finish #

While our pastes are colourized, the rest of the application still needs styling. We can serve static stylesheets through our application by adding a new endpoint to our `Pastebin` application that uses Werkzeug's `SharedDataMiddleware` to serve content out of our package:

```
from werkzeug import SharedDataMiddleware
# ...

# Any requests that get routed to shared_data that don't match a
# file in the appropriate package data directory will lead straight
# to a 404 Not Found response.
shared_data = SharedDataMiddleware(NotFound(), {
    '/styles': ('redpaste', 'styles')
})

#...
class Pastebin(WebApplication):
    # ...
    @get('/styles/<path>')
    def static_content(self, request, path):
        return shared_data
```

We'll also need a stylesheet to serve. Create the directory `redpaste/styles` and create `redpaste.css`:

```
html,
body {
    font-family: sans-serif;
    margin: 0;
    padding: 0;
}

html {
    height: 100%;
}

body {
    position: relative;
    min-height: 100%;
}

h1,
address {
    background: #cf0000;
    color: white;
}

h1 {
    padding: 0.5em;
}

address {
    font-style: normal;
    padding: 1em;
    position: absolute;
    bottom: 0;
    margin: 0;
}

address a:link,
address a:hover,
address a:visited,
address a:active {
    color: inherit;
}

#latest {
    float: left;
    width: 12em;
    margin: 0 1em;
}

#latest h2 {
    font-size: inherit;
    margin: 0 0 1em 0;
}

#latest ul {
    list-style: none;
}

#latest ul,
#latest li {
    margin: 0;
    padding: 0;
}

#paste,
#new {
    margin: 1em;
    margin-left: 14em;
}

#paste .highlight {
    background-color: #fff7f7;
}

#new {
    padding-bottom: 5em;
}

#new th {
    text-align: right;
}

#new td {
    text-align: left;
}

#new textarea {
    width: 100%;
}
```

We'll also need to add the new stylesheet to `redpaste/templates/layout.mako`'s `<head>` section, just like we did with the syntax highlighting stylesheets:

```
<head>
    <title>${self.page_title()}</title>
    <link rel="stylesheet" type="text/css" href="styles/redpaste.css">
    <link rel="stylesheet" type="text/css" href="styles/syntax/default">
</head>
```

In a production environment, you'll probably want to serve static content through Apache. While our application can serve content just fine, Apache's file service is much more efficient.

# Summary #

We're finally done. Our pastebin app works great, and it looks pretty good. It's all ready to package up as a `.egg` file or source tarball for distribution to others or for release to production. We've gone from a simple Hello World screen to a complete application that uses a number of libraries alongside Redfox. Where you go from here is up to you.

You can download the complete source to this example application from the Redfox [download page](http://code.google.com/p/python-redfox/downloads/list) or from [version control](http://code.google.com/p/python-redfox/source/browse?repo=redpaste).

There are a few things that could be added to this pastebin application to make it even better that are beyond the scope of this guide:

  * There's no spam protection whatsoever. Add a captcha.
  * The application doesn't remember who you are from paste to paste. Instead, it assumes you're the person who pasted the code you're looking at.
  * There's no parameter validation on the new paste `POST` handler.
  * There's no way (short of logging into the database) to delete a paste. Pastes don't expire, either.

Have fun!