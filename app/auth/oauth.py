from flask import current_app, url_for, redirect, session, request
from rauth import OAuth1Service, OAuth2Service
from hashlib import sha256
import random, string, urllib2, json


STATE = sha256(''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))).hexdigest()

print 'STATE is ', STATE

class OauthSignIn(object):
    providers = None

    def __init__(self, provider_name):
        self.provider_name = provider_name
        credentials = current_app.config['OAUTH_CREDENTIALS'][provider_name]
        self.consumer_id = credentials['id']
        self.consumer_secret = credentials['secret']

    def authorize(self):
       pass

    def callback(self):
        pass

    def callback_url(self):
        return url_for('auth.oauth_callback', provider=self.provider_name, _external=True)

    @classmethod
    def get_provider(cls, provider_name):
        if cls.providers is None:
            cls.providers = {}
            for provider_class in cls.__subclasses__():
                provider = provider_class()
                cls.providers[provider.provider_name] = provider
        return cls.providers[provider_name]

    def get_callback_url(self):
        return url_for('auth.oauth_callback', provider=self.provider_name,
                       _external=True)


class FacebookSignIn(OauthSignIn):
    def __init__(self):
        super(FacebookSignIn, self).__init__('facebook')
        self.service = OAuth2Service(
            name='facebook',
            client_id=self.consumer_id,
            client_secret=self.consumer_secret,
            authorize_url='https://graph.facebook.com/oauth/authorize',
            access_token_url='https://graph.facebook.com/oauth/access_token',
            base_url='https://graph.facebook.com/'

        )

    def authorize(self):
        session['state']= STATE


        return redirect(self.service.get_authorize_url(
            scope='email',
            response_type='code',
            redirect_uri=self.get_callback_url(),
            state=STATE
        ))

    def callback(self):
        if 'code' not in request.args:
            return None, None, None, None

        if request.args['state'] != session['state']:

            return None, None, None, None

        oauth_session = self.service.get_auth_session(
            data={'code': request.args['code'],
                  'grant_type': 'authorization_code',
                  'redirect_uri': self.get_callback_url()}
        )
        me = oauth_session.get('me?fields=id,email,picture.width(450).height(450)').json()
        #picture = oauth_session.get
        print me
        return (
            'facebook$' + me.get('id'), me.get('email').split('@')[0],
            me.get('email'), me.get('picture')
            )


class TwitterSignIn(OauthSignIn):
    def __init__(self):
        super(TwitterSignIn, self).__init__('twitter')
        self.service = OAuth1Service(
            name='twitter',
            consumer_key=self.consumer_id,
            consumer_secret=self.consumer_secret,
            request_token_url='https://api.twitter.com/oauth/request_token',
            authorize_url='https://api.twitter.com/oauth/authorize',
            access_token_url='https://api.twitter.com/oauth/access_token',
            base_url='https://api.twitter.com/1.1/'

        )

    def authorize(self):
        request_token = self.service.get_request_token(
            params={'oauth_callback':self.get_callback_url()}
        )
        session['request_token'] = request_token
        return redirect(self.service.get_authorize_url(request_token[0]))

    def callback(self):
        request_token = session.pop('request_token')
        if 'oauth_verifier' not in request.args:
            return None, None, None, None

        oauth_session = self.service.get_auth_session(
            request_token[0],
            request_token[1],
            data={'oauth_verifier': request.args['oauth_verifier']}
        )
        me = oauth_session.get('account/verify_credentials.json').json()
        social_id = 'twitter$' + str(me.get('id'))
        username = me.get('screen_name')
        return social_id, username, None, None  # twitter does not provide email

class GoogleSignIn(OauthSignIn):
    def __init__(self):
        super(GoogleSignIn, self).__init__('google')
        googleinfo = urllib2.urlopen('https://accounts.google.com/.well-known/openid-configuration')
        google_params = json.load(googleinfo)
        self.service = OAuth2Service(
            name='google',
            client_id= self.consumer_id,
            client_secret = self.consumer_secret,
            authorize_url=google_params.get('authorization_endpoint'),
            base_url=google_params.get('userinfo_endpoint'),
            access_token_url = google_params.get('token_endpoint')
        )

    def authorize(self):
        return redirect(self.service.get_authorize_url(
            scope = 'email',
            response_type = 'code',
            redirect_uri = self.get_callback_url()
        ))

    def callback(self):
        if 'code' not in request.args:
            return None, None, None, None
        oauth_session = self.service.get_auth_session(
            data = {'code': request.args['code'],
                    'grant_type': 'authorization_code',
                    'redirect_uri': self.get_callback_url()},

            decoder = json.loads
        )
        me = oauth_session.get('').json()
        print me
        return 'google$'+me['sub'],me['name'], me['email'], None