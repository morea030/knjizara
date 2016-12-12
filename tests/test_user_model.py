import unittest
from app.models import User, Role, Permission, AnnonymousUser
from app import create_app, db
import time


class UserModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app=create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_setter(self):
        u = User(password = 'cat')
        self.assertTrue(u.password_hash is not None)

    def test_no_password_getter(self):
        u = User(password = 'cat')
        with self.assertRaises(AttributeError):
            u.password

    def test_password_verification(self):
        u = User(password = 'cat')
        self.assertTrue(u.verify_password('cat'))
        self.assertFalse(u.verify_password('dog'))

    def test_password_salts_are_random(self):
        u = User(password='cat')
        u2 = User(password='cat')
        self.assertTrue(u.password_hash != u2.password_hash)

    def test_valid_confirmation_token(self):
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_confirmation_token()
        self.assertTrue(u.confirm(token))

    def test_invalid_confirmation_token(self):
        u1 = User(password="cat")
        u2 = User(password="dog")
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        token = u1.generate_confirmation_token()
        self.assertFalse(u2.confirm(token))

    def test_expiered_confirmation_token(self):
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        token=u.generate_confirmation_token(1)
        time.sleep(2)
        self.assertFalse(u.confirm(token))

    def test_valid_reset_token(self):
        u = User(password="cat")
        db.session.add(u)
        db.session.commit()
        token = u.generate_reset_token()
        self.assertTrue(u.reset_password(token, 'dog'))
        self.assertTrue(u.verify_password('dog'))

    def test_invalid_reset_token(self):
        u1 = User(password="cat")
        u2 = User(password='dog')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        token = u1.generate_reset_token()
        self.assertFalse(u2.reset_password(token, 'donkey'))
        self.assertTrue(u2.verify_password('dog'))

    def test_valid_email_change(self):
        u = User(email='john@example.co', password="cat")
        db.session.add(u)
        db.session.commit()
        token = u.generate_email_change_token("voja@voja.com")
        self.assertTrue(u.change_email(token))
        self.assertTrue(u.email =='voja@voja.com')

    def test_invalid_email_change_token(self):
        u1 = User(email='john@example.com', password="cat")
        u2 = User(email='susan@example.org', password="moose")
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        token = u1.generate_email_change_token("voja@voja.oom")
        self.assertFalse(u2.change_email(token))
        self.assertTrue(u2.email == 'susan@example.org')

    def test_duplicate_email_change_token(self):
        u1 = User(email='john@example.com', password="cat")
        u2 = User(email='susan@example.org', password="moose")
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        token = u1.generate_email_change_token("susan@example.org")
        self.assertFalse(u1.change_email(token))
        self.assertTrue(u1.email == 'john@example.com')

    def test_roles_and_permissions(self):
        Role.insert_roles()
        u = User(email="john@example.com", password ="cat")
        self.assertTrue(u.can(Permission.WRITE_ARTICLES))
        self.assertFalse(u.can(Permission.MODERATE_COMMENTS))

    def test_anonymous_user(self):
        u =AnnonymousUser()
        self.assertFalse(u.can(Permission.WRITE_ARTICLES))
