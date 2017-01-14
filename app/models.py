# python run.py db migrate
# python run.py db upgrade
# inititalization python run.py db init

from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, AnonymousUserMixin
from . import login_manager
from itsdangerous import TimedJSONWebSignatureSerializer as serializer
from flask import current_app, request, url_for
from datetime import datetime
import hashlib
# from markdown import markdown
import bleach
import urllib2
# from slugify import slugify
import flask_whooshalchemy as whooshalchemy


class FollowItems(db.Model):
    __tablename__ = 'follow_item'
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('knjige.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class FollowAuthors(db.Model):
    __tablename__ = 'follow_authors'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('authors.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)



class Knjige(db.Model):
    __tablename__ = "knjige"
    __searchable__ = ['naziv']
    id = db.Column(db.Integer, primary_key=True)
    naziv = db.Column(db.VARCHAR(256), )
    #autor = db.Column(db.VARCHAR(256))
    autor = db.Column(db.Integer, db.ForeignKey('authors.id'))
    zanr = db.Column(db.VARCHAR(256))
    cene = db.relationship('Source', backref='naziv', lazy='dynamic')
    post = db.relationship('Post', backref='knjiga', lazy='dynamic')
    followed = db.relationship('FollowItems', foreign_keys=[FollowItems.followed_id],
                               backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic', cascade='all, delete-orphan')

    isbn = db.Column(db.VARCHAR(64))
    timestamp = db.Column(db.DateTime)

class Source(db.Model):
    __tablename__ = "source"
    id = db.Column(db.Integer, primary_key=True)
    cena = db.Column(db.VARCHAR(64))
    website = db.Column(db.VARCHAR(128))
    opis = db.Column(db.Text)
    knjiga = db.Column(db.Integer, db.ForeignKey('knjige.id'))
    slika = db.Column(db.VARCHAR(128))
    knjizara = db.Column(db.VARCHAR(64))
    knjizara_sajt = db.Column(db.VARCHAR(128))





class Authors(db.Model):
    __tablename__='authors'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.VARCHAR(256))
    books = db.relationship('Knjige', backref='author', lazy='dynamic')
    followers = db.relationship('FollowAuthors', foreign_keys=[FollowAuthors.author_id],
                               backref=db.backref('authors', lazy='joined'),
                               lazy='dynamic', cascade='all, delete-orphan')




class Follow(db.Model):
    __tablename__ = 'follow'
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key = True)
    followed_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class User(UserMixin,db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True)
    social_id = db.Column(db.String(64), unique=True)
    password_hash = db.Column(db.String(128))
    email = db.Column(db.String(120), index=True, unique=True)
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    confirmed = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(128))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text)
    image = db.Column(db.String(64))
    social_image = db.Column(db.String(265))
    avatar_hash = db.Column(db.String(32))
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    followed = db.relationship('Follow', foreign_keys=[Follow.follower_id], backref=db.backref('follower', lazy='joined'),
                                  lazy='dynamic', cascade = 'all, delete-orphan')
    followers = db.relationship('Follow', foreign_keys=[Follow.followed_id], backref=db.backref('followed', lazy= 'joined'),
                                lazy = 'dynamic', cascade='all, delete-orphan')
    following_item = db.relationship('FollowItems', foreign_keys=[FollowItems.follower_id], backref=db.backref('follower_item', lazy= 'joined'),
                                lazy = 'dynamic', cascade='all, delete-orphan')
    followed_author = db.relationship('FollowAuthors', foreign_keys=[FollowAuthors.user_id],
                               backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic', cascade='all, delete-orphan')

    comments = db.relationship('Comment', backref='author', lazy='dynamic')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        self.follow(self, 'user')
        if self.role is None:
            if self.email == current_app.config['KNJIZARA_ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default = True).first()
        if self.avatar_hash is None and self.image is None:
            if self.email is not None:
                self.avatar_hash= hashlib.md5(self.email.encode('utf-8')).hexdigest()
            else:
                self.avatar_hash = hashlib.md5(self.social_id.encode('utf-8')).hexdigest()


    @property
    def password(self):
        raise AttributeError('password is not a readable property')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        s = serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset':self.id})

    def reset_password(self, token, new_password):
        s = serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = serializer(current_app.config["SECRET_KEY"], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})

    def change_email(self, token):
        s = serializer(current_app.config["SECRET_KEY"])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email = new_email).first() is not None:
            return False
        self.email = new_email
        db.session.add(self)
        return True

    def can(self, permissions):
        print "can"
        return self.role is not None and \
               (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def gravatar(self, size=100, default='wavatar', rating='g'):
        if self.image is None and self.social_image is None:
            if request.is_secure:
                url = 'https://secure.gravatar.com/avatar'
            else:
                url = 'http://gravatar.com/avatar'
            hash = self.avatar_hash
            return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
                url=url, hash=hash, size=size, default=default, rating=rating)

        if self.image is None:
            return self.social_image
        return url_for('static', filename='uploads/{image}'.format(image=self.image))

    def follow(self, user, type):
        print 'Follow'
        f = None
        if type == 'user':
            if not self.is_following(user, type):
                f = Follow(follower=self, followed = user)
        elif type == 'item' or type == 'author':
            print 'Follow item'
            if not self.is_following(user, type):
                print 'is not following'
                if type == 'item':
                    f = FollowItems(follower_item=self, followed_id=user.id)
                elif type == 'author':
                    f = FollowAuthors(follower=self, author_id=user.id)
        if f:
            db.session.add(f)

    def unfollow(self, user, type):
        f = None
        if type == 'User':
            f = self.followed.filter_by(followed_id=user.id).first()
        elif type == 'naziv':
            f = self.following_item.filter_by(followed_id=user.id).first()
        elif type == 'author':
            f = self.followed_author.filter_by(author_id=user.id).first()
        if f:
            db.session.delete(f)

    def is_following(self, user, type):
        if type == 'user':
            return self.followed.filter_by(followed_id=user.id).first() is not None
        elif type == 'item':
            print "ITEM"
            return self.following_item.filter_by(followed_id=user.id).first() is not None
        elif type == 'author':
            return self.followed_author.filter_by(author_id=user.id).first() is not None
        else:
            return False

    def is_followed(self, user):
        return self.followers.filter(follower_id=user.id).first() is not None

    @property
    def followed_posts(self):
        return Post.query.join(Follow, Follow.followed_id == Post.user_id)\
                .filter(Follow.follower_id == self.id)

    @property
    def followed_items(self):
        return Post.query.join(FollowItems, FollowItems.followed_id == Post.book_id)\
                .filter(FollowItems.follower_id == self.id)
    @property
    def followed_authors(self):
        # return db.session.query(Knjige, Post).join( FollowAuthors, FollowAuthors.author_id==Knjige.autor ).join(Post, Post.book_id==Knjige.id)\
        #     .filter(FollowAuthors.user_id==self.id)#Dovrsiti folow autor do autora autor do knjige knjiga do posta

        # return Post.query.join(FollowAuthors, FollowAuthors.author_id == Post.knjiga.any(autor))\
        #     .filter_by(FollowAuthors.user_id == self.id)
        return Post.query.join(Knjige, Knjige.id == Post.book_id).join(FollowAuthors,
                                                               FollowAuthors.author_id == Knjige.autor).filter(FollowAuthors.user_id == self.id)

    @staticmethod
    def generate_fake(count=100):
        """Creating dummy users, via forgerypy library"""
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py

        seed()
        for i in range(count):
            u = User(email=forgery_py.internet.email_address(),
                     username = forgery_py.internet.user_name(),
                     password = forgery_py.lorem_ipsum.word(),
                     confirmed = True,
                     name = forgery_py.name.full_name(),
                     location = forgery_py.address.city(),
                     about_me= forgery_py.lorem_ipsum.sentence(),
                     member_since = forgery_py.date.date())
            db.session.add(u)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.roleback()

    @staticmethod
    def add_self_follows():
        """Updating exosting users to self-follow"""
        for user in User.query.all():
            if not user.is_following(user):
                user.follow(user)
                db.session.add(user)
                db.session.commit()


    def __repr__(self):
        return '<User %r>' % (self.name)


class AnnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

login_manager.anonymous_user = AnnonymousUser




class Post(db.Model):
    __tablename__='post'

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index = True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    body_html= db.Column(db.Text)
    comments = db.relationship('Comment', backref='post', lazy='dynamic')
    book_id = db.Column(db.Integer, db.ForeignKey('knjige.id'))
    #slug = db.Column(db.String(64))

    # def __init__(self, *args, **kwargs):
    # Kod za kreiranje i upisivanje slug-a u db.
    #     super(Post, self).__init__(*args, **kwargs)
    #     if not 'slug' in kwargs:
    #         kwargs['slug']=slugify(kwargs.get('title', ''))



    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'b', 'blockquote', 'code', 'em', 'i', 'li', 'ol', 'pre', 'strong',
                        'ul', 'h1', 'h2', 'h3', 'p', 'img', 'strike', 'span']
        attrs = {'a': ['href'], 'img': filter_src, 'span': ['style']}  # should dissallow external img src,
        # or img tags alltogether
        target.body_html = bleach.linkify(bleach.clean(value,
                                                       tags = allowed_tags, attributes=attrs, protocols=['http', 'https'], strip=True))




    @staticmethod
    def generate_fake(count=100):
        """Generates dummy posts. Use it from shell(python run.py shell, Post.generate_fake(100)"""

        from random import seed, randint
        import forgery_py

        seed()
        user_count = User.query.count()
        for i in range(count):
            u = User.query.offset(randint(0,user_count-1)).first()

            p = Post(body=forgery_py.lorem_ipsum.sentences(randint(1,8)),
                     timestamp = forgery_py.date.date(True),
                     author = u)
            db.session.add(p)
            db.session.commit()

    def __repr__(self):
        return '<Post %r' % (self.body)

db.event.listen(Post.body, 'set', Post.on_changed_body)
#whooshalchemy.whoosh_index(app, Post)


class HeadRequest(urllib2.Request):
    def get_method(self):
        return 'HEAD'

def filter_src(name, value):
    print
    print 'FILTER SRC'
    print
    if name in ('alt', 'height', 'weight'):
        return True
    if name == 'src':
        if image_type(value):
            print "TRUE"
            return True

def image_type(url):
    valid_types = ('image/png', 'image/jpeg', 'image/gif', 'image/jpg')
    try:
        response = urllib2.urlopen(HeadRequest(url))
        maintype = response.headers['Content-Type'].split(':')[0].lower()
        print maintype
        if maintype in valid_types:
            return True
        return False
    except:
        return False



class Role(db.Model):
    """This table implements the user roles(User, Moderator, Admin).
    Asigned to each role are set of premissions, implemented as
    bit values in Permission class. When a new user signs in he gets assigned the default role
    which in this case is set to be User"""
    __tablename__='roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        """Populates the role table"""
        roles = {
            'User': (Permission.FOLLOW |
                     Permission.COMMENT |
                     Permission.WRITE_ARTICLES, True),
            'Moderator': (Permission.FOLLOW |
                          Permission.COMMENT |
                          Permission.WRITE_ARTICLES |
                          Permission.MODERATE_COMMENTS, False),
            'Administrator': (0xff, False)
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()


class Permission:
    FOLLOW = 0X01
    COMMENT = 0X02
    WRITE_ARTICLES = 0X04
    MODERATE_COMMENTS = 0X08
    ADMINISTER = 0X80


class Comment(db.Model):
    __tablename__='comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    disabled = db.Column(db.Boolean)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    parrent_id = db.Column(db.Integer, db.ForeignKey('comments.id'))
    parrent = db.relationship('Comment', remote_side=[id], backref=db.backref('child', lazy='dynamic'))

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'b', 'acronym' 'blockquote', 'code', 'em', 'i', 'li', 'ol', 'pre', 'strong',
                            'ul', 'h1', 'h2', 'h3', 'p', 'strike', 'span']
        attrs = {'a': ['href'], 'span': ['style']}  # should dissallow external img src,
        # or img tags alltogether
        target.body_html = bleach.linkify(bleach.clean(value,
            tags = allowed_tags, attributes=attrs, protocols=['http', 'https'], strip=True))    

    @staticmethod    
    def get_children(id, count = 0):
        """Counts all descendants for given node, ie all subcomments of a given comment"""
        parrent = Comment.query.filter_by(id=id).first()
        if parrent.child.all():    
            descendants =  parrent.child.all()
            for descendant in descendants:
                count +=1
                count = Comment.get_children(descendant.id, count=count) 
        else:
            return count       
        return count      
        


db.event.listen(Comment.body, 'set', Comment.on_changed_body)



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))