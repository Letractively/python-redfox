"""Provides routable-endpoint manipulations, including the ``@route``,
``@get``, ``@post``, ``@put``, and ``@delete`` decorators.
"""

from functools import partial

def make_routable(target):
    """Ensures that a target is routable. If the target is already
    routable, nothing happens.
    """
    if not is_routable(target):
        target.__rule_args__ = []

def is_routable(target):
    """Returns ``True`` if and only if the passed target is routable."""
    return hasattr(target, '__rule_args__')

def routes(target, *extra_args, **extra_kwargs):
    """Retrieves the route definitions for a target, optionally adding
    extra parameters to each route. If called on a non-routable target,
    returns an empty sequence; otherwise, returns a sequence of
    ``(arg, kwarg)`` tuples, one for each route."""
    if is_routable(target):
        for args, kwargs in target.__rule_args__:
            yield (args + extra_args), dict(kwargs, **extra_kwargs)

def route(*args, **kwargs):
    """Creates a decorator that makes target objects routable. The
    parameters passed to ``@route`` will be stored in the new route
    definition and returned by ``routes(target)``.
    """
    def decorate_target(target):
        make_routable(target)
        target.__rule_args__.append((args, kwargs))
        return target
    return decorate_target

# The following partial applications of route are only useful if you're
# building Werkzeug Rule objects, as they rely on specifics of the Rule
# parameter list.

# Convenience version of ``@route`` that adds ``methods=['GET']`` to
# the route definition.
get = partial(route, methods=['GET'])
# Convenience version of ``@route`` that adds ``methods=['POST']`` to
# the route definition.
post = partial(route, methods=['POST'])
# Convenience version of ``@route`` that adds ``methods=['PUT']`` to
# the route definition.
put = partial(route, methods=['PUT'])
# Convenience version of ``@route`` that adds ``methods=['DELETE']`` to
# the route definition.
delete = partial(route, methods=['DELETE'])
