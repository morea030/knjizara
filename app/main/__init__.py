from flask import Blueprint
from ..models import Permission

main = Blueprint('main', __name__)

from . import views, errors


@main.app_context_processor
def inject_permissions():
    return dict(Permission = Permission)
# app = Flask(__name__)
# #app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
# app.config.from_object('config')
#
# db = SQLAlchemy(app)
# migrate = Migrate(app, db)
# bootstrap = Bootstrap(app)
# moment = Moment(app)
# mail = Mail(app)
#app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

#from app import views, models  # the reason this is at the end of the file  is to avoid circular references,
# because the views module needs to import the app variable defined in this script.
