from flask_wtf import FlaskForm as Form
from wtforms import StringField, BooleanField, SubmitField, TextAreaField, SelectField, RadioField
from wtforms.validators import DataRequired, Email,Length, Regexp, ValidationError
from ..models import Role, User
from flask_wtf.file import FileAllowed, FileField
from flask_pagedown.fields import PageDownField

from wtforms.fields.html5 import EmailField
from .. import photos

class EditProfileForm(Form):
    name = StringField('Real name', validators=[Length(0,64)])
    location = StringField('Location', validators = [Length(0,64)])
    about_me = TextAreaField('About Me')
    picture = FileField('picture', validators=[FileAllowed(photos, 'Images only!')])
    remove_picture = BooleanField('Remove picture')
    submit = SubmitField('Submit')



class EditProfileAdminForm(Form):
    email = StringField('Email', validators=[DataRequired(), Length(1,64), Email()])
    username = StringField('Username', validators=[DataRequired(), Length(1,64),
                                                   Regexp('^[A-Za-z][A-Za-z0-9_.]*$',
                                                          0, 'Usernames must have only letters,'
                                                             'numbers, dots, or underscores')])
    confirmed = BooleanField('Confirmed')
    role= SelectField('Role', coerce=int)
    name = StringField('Real name', validators=[Length(0,64)])
    location = StringField('Location', validators=[Length(0,64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and User.query.filter_by(email=field.data).first():
            raise ValidationError('Email allready in use')

    def validate_username(self, field):
        if field.data != self.user.username and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError('Username allready in use')

class PostForm(Form):
    body = PageDownField('Whats on your mind', validators=[DataRequired()])
    submit = SubmitField('Submit')

class CommentForm(Form):
    body = StringField('', validators=[DataRequired()])
    submit = SubmitField('Submit')    

class SearchForm(Form):
    search = StringField('search', validators = [DataRequired()],  render_kw={"placeholder": "Unesite ime knjige"})
       