import os
from flask import url_for
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    WTF_CSPRF_ENABLED = True
    SECRET_KEY = "Igo16Jel14Ira12NewBlueMoon"
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    KNJIZARA_MAIL_SUBJECT_PREFIX = '[Knjizara]'
    KNJIZARA_MAIL_SENDER = 'Knjizara Admin <igorjosic@gmail.com>'
    KNJIZARA_ADMIN = 'igorjosic@gmail.com'
    POSTS_PER_PAGE = 10
    FOLLOWERS_PER_PAGE = 10
    COMMENTS_PER_PAGE = 10
    UPLOADED_PHOTOS_DEST = 'app/static/uploads'
    PHOTO_ABSOLUTE = os.path.join(basedir,  )
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_RECORD_QUERIES = True
    MAX_SEARCH_RESULTS = 50
    OAUTH_CREDENTIALS ={
        'facebook':{
            'id': '1779440718972979',
            'secret': '88fc8f085943f6d967816fe3740fd389'
        },
        'twitter': {
            'id':'DMJ3hsglhzkHf31M48pf7vxiY',
            'secret':'shqKHe6jlvGgTtpo7ru1ccDj8UHbKNSql7mM4QV0gr1P1HPaRE'
        },
        'google':{
            'id': '30800319835-4gcjh6dlbb3e5tp9rginp09smlo13c1s.apps.googleusercontent.com',
            'secret': 'iCBCO37SBL7nw13BSL9ePz7F'
        }
    }

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'igorjosic@gmail.com'  # os.environ.get('GMAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('GMAIL_PASSWORD')
    SQLALCHEMY_DATABASE_URI = 'mysql://root:Igojelira1208@localhost/knjizara'
    SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
    WHOOSH_BASE = os.path.join(basedir, 'whoosh_index')
    
class TestConfig(Config):
    Testing = True
    SQLALCHEMY_DATABASE_URI = 'mysql://root:Igojelira1208@localhost/test_knjizara'


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')


config = {
    'development': DevelopmentConfig,
    'testing': TestConfig,
    'production': ProductionConfig,

    'default': DevelopmentConfig
}













