from . import main
from flask import render_template

@main.errorhandler(404)
def page_not_found(e):
    print "not found"
    return render_template('404.html'), 404


# @main.app.errorhandler(500)
# def internal_server_error(e):
#     return render_template('500.html'), 500