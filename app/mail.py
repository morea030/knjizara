from app import mail
from flask.ext.mail import Message

from threading import Thread
from main import main
from flask import current_app, render_template

def send_async_email(app, msg):

    with app.app_context():
        mail.send(msg)


def send_mail(to, subject, template, **kwargs):
    app = current_app._get_current_object()
    msg =Message(app.config['KNJIZARA_MAIL_SUBJECT_PREFIX'] + subject,
                 sender=app.config['KNJIZARA_MAIL_SENDER'], recipients=[to])

    name = kwargs.get('name')
    token = kwargs.get('token')
    msg.body = render_template(template + '.txt', name=name, token = token)
    msg.html= render_template(template + '.html', name=name, token = token )
    # mail.send(msg)
    thr = Thread(target = send_async_email, args=[app, msg])
    thr.start()
    return thr

