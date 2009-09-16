from werkzeug import Request as WerkzeugRequest, BaseRequest

class MapAdapterMixin(object):
    def __init__(self, map_adapter):
        self.map_adapter = map_adapter

    def build(self, endpoint, values=None, method=None, force_external=False):
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
        return self.map_adapter.dispatch(
            view_func=view_func,
            path_info=path_info,
            method=method,
            catch_http_exceptions=catch_http_exceptions
        )
    
    def test(self, path_info=None, method=None):
        return self.map_adapter.test(path_info=path_info, method=method)
    
    def match(self, path_info=None, method=None):
        return self.map_adapter.match(path_info=path_info, method=method)
    
    def match_url(self, url, method=None):
        # See <http://dev.pocoo.org/projects/werkzeug/ticket/414>
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
    def __init__(self, map_adapter, *args, **kwargs):
        MapAdapterMixin.__init__(self, map_adapter)
        WerkzeugRequest.__init__(self, *args, **kwargs)
