from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from config import config
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_uploads import UploadSet, configure_uploads, IMAGES
from flask_pagedown import PageDown
import flask_whooshalchemy as whooshalchemy
from flask_socketio import SocketIO
from flask_wtf.csrf import CsrfProtect

bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()
migrate = Migrate()
login_manager=LoginManager()
login_manager.session_protection='basic'
login_manager.login_view='auth.login'
photos = UploadSet('photos', IMAGES)
pagedown = PageDown()
socketio = SocketIO()
async_mode=None
csfr =CsrfProtect()

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    #mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    configure_uploads(app, photos)
    pagedown.init_app(app)
    socketio.init_app(app, async_mode=async_mode)
    csfr.init_app(app)
    from models import Knjige
    whooshalchemy.whoosh_index(app, Knjige)


    from main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    return app