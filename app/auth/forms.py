from flask.ext.wtf import FlaskForm as Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Email, Length, EqualTo, Regexp
from ..models import User


class LoginForm(Form):
    email = StringField('Email', validators=[DataRequired(),Length(1,64),
                                             Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log in')

class RegistrationForm(Form):
    email=StringField('Email', validators=[DataRequired(), Length(1,64), Email()])
    username=StringField('Username', validators=[DataRequired(), Length(1,64),
                                                 Regexp('^[A-Za-z][A-Za-z0-9_.]*$',0,
                                                        'Usernames must'
                                                              'have only letters,'
                                                              'numbers, dots '
                                                              'or underscores')])
    password = PasswordField('Password', validators=[DataRequired(), EqualTo('password2',
                                                                           message='Passwords '
                                                                                   'must match')])
    password2 = PasswordField('Confirm password', validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered')

    def validate_username(self, field):
        if User.query.filter_by(username = field.data).first():
            raise ValidationError('Username allready in use')


class ChangePasswordForm(Form):
    old_password = PasswordField('old password', validators=[DataRequired()])
    password = PasswordField('New Password',
                             validators=[DataRequired(),
                                         EqualTo('password2',
                                                 message='Passwords must match')])
    password2 = PasswordField('Confirm New Password', validators=[DataRequired()])
    submit = SubmitField('Update Password')


class PasswordResetRequestForm(Form):
    email=StringField('Email', validators=[DataRequired(), Length(1,64), Email()])
    submit=SubmitField('Reset Password')

class PasswordResetForm(Form):
    email = StringField('Email', validators=[DataRequired(), Length(1,64), Email()])
    password=PasswordField('New Password', validators=[DataRequired(), EqualTo('password2',
                                                                               message='Passwords '
                                                                                       'must match')])
    password2 = PasswordField('Confirm password', validators=[DataRequired()])
    submit = SubmitField('Reset Password')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError('Unknown email address')

# When a form defines a method with the prefix validate_  followed
#  by the name of a field, the method
# is invoked in addition to any regularly defined validators.

class ChangeEmailForm(Form):
    email = StringField('New Email', validators=[DataRequired(), Length(1,64),
                                                 Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Update Email Address')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered')


