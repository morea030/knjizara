from flask import render_template, request, redirect, url_for, flash
from . import auth
from flask.ext.login import login_user, logout_user, login_required, current_user, fresh_login_required
from ..models import User
from .forms import LoginForm, RegistrationForm, ChangePasswordForm, PasswordResetForm,\
    PasswordResetRequestForm, ChangeEmailForm
from .. import db
from ..mail import send_mail
from .oauth import OauthSignIn
from hashlib import sha256
import json
from datetime import datetime
# TODO implement fresh login requiered for changig delicate user info such as email and password
# TODO implement securely redirect back check this snippet http://flask.pocoo.org/snippets/62/

@auth.route('/login', methods = ["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('Invalid username or password')

    return render_template('auth/login.html', form = form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out')
    return redirect(url_for('main.index'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user= User(username=form.username.data, email=form.email.data,
                   password = form.password.data, member_since = datetime.utcnow())
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_mail(user.email, 'Confirm your Account', 'auth/email/confirm',
                  user = user, token = token)

        flash('A confirmation email has been  sent to you by email.')
        return redirect(url_for('main.index'))
    return render_template('auth/register.html', form=form)


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash('you have confirmed your user account. Thanks!')
    else:
        flash('The confirmation link is invalid or has expired')
    return redirect(url_for('main.index'))


@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed \
                and request.endpoint[:5] != 'auth.':
            return redirect(url_for('auth.unconfirmed'))


@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect('main.index')
    return render_template('auth/unconfirmed.html')


@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_mail(current_user.email, 'Confirm your account', 'auth/email/confirm', name=current_user,
              token=token)
    flash('A new confirmation email has been sent to you by email')
    return redirect(url_for('main.index'))


@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            flash('Your password has been updated')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid password')
    return render_template('auth/change_password.html', form=form)


@auth.route('/reset', methods=['GET', 'POST'])
def password_reset_request():
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token= user.generate_reset_token()
            send_mail(user.email, 'Reset Your Password', 'auth/email/reset_password',
                      user=user, token=token, next=request.args.get('next'))
            flash('An email with instructions to reset your password has been sent to you')
            return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)


@auth.route('/reset/<token>', methods=["GET", "POST"])
def password_reset(token):
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetForm
    if form.validate_on_submit():
        user=User.query.filter_by(email=form.email.data).first()
        if user is None:
            return redirect(url_for('main.index'))
        if user.reset_password(token, form.password.data):
            flash('Your password has been updated')
            return redirect(url_for('auth.login'))
        else:
            return redirect(url_for('main.index'))
    return render_template('auth/reset_password.html', form=form)


@auth.route('/change-email', methods=['GET', 'POST'])
@login_required
def change_email_request():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        if current_user.verify.password(form.password.data):
            new_email = form.email.data
            token = current_user.generate_email_change_token(new_email)
            send_mail(new_email, 'Confirm your email address',
                      'auth/email/change_email', user=current_user,
                      token=token)
            flash('An email with instructions to confirm your new email'
                  'has been sent to you')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid email or password')
    return render_template('auth/change_email.html', form=form)


@auth.route('/change-email/<token>', methods=["GET","POST"])
@login_required
def change_email(token):
    if current_user.change_email(token):
        flash('Your email address has been updated')
    else:
        flash('Invalid request')
    return redirect(url_for('main.index'))


@auth.route('/authorize/<provider>')
def oauth_authorize(provider):

    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    oauth = OauthSignIn.get_provider(provider)
    print oauth
    return oauth.authorize()


@auth.route('/callback/<provider>')
def oauth_callback(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    oauth = OauthSignIn.get_provider(provider)
    social_id, username, email, picture = oauth.callback()
    #print picture['data']['url']
    if social_id is None:
        flash('Authentication failed')
        return redirect(url_for('main.index'))
    user = User.query.filter_by(social_id=social_id).first()
    if not user:
        u = User.query.filter_by(email=email).first()
        if u:
            flash('Vec postoji nalog sa vasom imejl adresom')
            return redirect(url_for('main.index'))
        try:
            social_image=picture['data']['url']
        except:
            social_image= None

        user = User(social_id=social_id, username=username, email=email, confirmed=True, social_image=social_image,
                    member_since=datetime.utcnow())
        db.session.add(user)
        db.session.commit()
    login_user(user, remember=True)
    return redirect(url_for('main.index'))
