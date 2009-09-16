from werkzeug import Request as WerkzeugRequest, BaseRequest

class MapAdapterMixin(object):
    """A request mixin that exposes a Werkzeug MapAdapter and its operations."""
    
    def __init__(self, map_adapter):
        self.map_adapter = map_adapter

    def build(self, endpoint, values=None, method=None, force_external=False):
        """Delegates to ``MapAdapter.build``."""
        return self.map_adapter.build(
            endpoint=endpoint,
            values=values,
            method=method,
            force_external=force_external
        )
    
    def dispatch(
        self,
        view_func,
        path_info=None,
        method=None,
        catch_http_exceptions=False
    ):
        """Delegates to ``MapAdapter.dispatch``."""
        return self.map_adapter.dispatch(
            view_func=view_func,
            path_info=path_info,
            method=method,
            catch_http_exceptions=catch_http_exceptions
        )
    
    def test(self, path_info=None, method=None):
        """Delegates to ``MapAdapter.test``."""
        return self.map_adapter.test(path_info=path_info, method=method)
    
    def match(self, path_info=None, method=None):
        """Delegates to ``MapAdapter.match``."""
        return self.map_adapter.match(path_info=path_info, method=method)
    
    def match_url(self, url, method=None):
        """Delegates to ``MapAdapter.match_url``, if available, or implements
        it locally otherwise. See Werkzeug ticket #414 for details."""
        parsed_url = urlsplit(url)
        if self.subdomain:
            netloc = '%s.%s' % (self.subdomain, self.server_name)
        else:
            netloc = self.server_name        
        if any((
            parsed_url.scheme and parsed_url.scheme != self.url_scheme,
            parsed_url.netloc and parsed_url.netloc != netloc,
            not parsed_url.path.startswith(self.script_name)
        )):
            raise NotFound()
        path_info = parsed_url.path[len(self.script_name):]
        if parsed_url.query:
            path_info = "%s?%s" % (path_info, parsed_url.query)
        return self.match(path_info, method=method)

class Request(WerkzeugRequest, MapAdapterMixin):
    """A request type containing all of the types covered by
    ``werkzeug.Request`` as well as ``MapAdapterMixin`` from this
    module."""
    def __init__(self, map_adapter, *args, **kwargs):
        MapAdapterMixin.__init__(self, map_adapter)
        WerkzeugRequest.__init__(self, *args, **kwargs)
