from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def user_role(function):
    def wrap(request, *args, **kwargs):
        if request.user.user_type == 'NOIC_STAFF':
            return function(request, *args, *kwargs)
        else:
            raise PermissionDenied

    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap
