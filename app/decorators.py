from functools import wraps
from flask import abort
from flask.ext.login import current_user
from models import Permission


def permission_required(permisssion):
    def deocrator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.can(permisssion):
            	print "Can it?"
            	print current_user.can(permission)
                abort(403)
            print "probably can"    
            return f(*args, **kwargs)
        return decorated_function
    return deocrator


def admin_required(f):
    return permission_required(Permission.ADMINISTER)(f)


