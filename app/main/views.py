# not covered in book https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xiv-i18n-and-l10n
from . import main
from ..mail import send_mail
from flask import render_template, flash, redirect, request, abort, url_for, current_app, make_response
from datetime import datetime
from ..models import User, Role, Permission, Post, Comment
from flask_login import login_required, current_user
from forms import EditProfileForm, EditProfileAdminForm, PostForm, CommentForm
from ..  import db
from ..decorators import admin_required, permission_required
from .. import photos
from werkzeug.utils import secure_filename
import  os


@main.route('/', methods=['GET', 'POST'])
@main.route('/index', methods=['GET', 'POST'])
def index():
    form = PostForm()

    if current_user.can(Permission.WRITE_ARTICLES) and form.validate_on_submit():
        print "HIT"
        post = Post(body = form.body.data, author=current_user._get_current_object(), timestamp=datetime.utcnow())
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('.index'))
    #posts = Post.query.order_by(Post.timestamp.desc()).all()
#pagination = Post.query.order_by(Post.timestamp.desc()).paginate(page, per_page=current_app.config['POSTS_PER_PAGE'],
                                                                     # error_out=False)
    #posts = pagination.items

    show_followed = False
    page = request.args.get('page', 1, type=int)
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get('show_followed', ''))
    if show_followed:
        query=current_user.followed_posts
    else:
        query = Post.query
    pagination =  query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['POSTS_PER_PAGE'], error_out=False)          
    posts = pagination.items

    return render_template("index.html",form=form, posts=posts, current_time=datetime.utcnow(), show_followed=show_followed, pagination=pagination)




@main.route('/all')
@login_required
def show_all():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '', max_age=30*24*60*60)
    return resp


@main.route('/followed')
@login_required
def show_followed():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '1', max_age=30*24*60*60)
    return resp


@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    posts = user.posts.order_by(Post.timestamp.desc()).all()
    return render_template('user.html', user=user, posts=posts)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        print "VALIDATE"
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        filename = secure_filename(form.picture.data.filename)
        delete_picture = form.remove_picture.data
        print filename
        if delete_picture:
            if current_user.image is not None:
                os.remove(os.path.join(current_app.config['UPLOADED_PHOTOS_DEST'], current_user.image))
            current_user.image = None
            current_user.social_image = None

        if current_user.image is not None and filename:
            os.remove(os.path.join(current_app.config['UPLOADED_PHOTOS_DEST'], current_user.image))

        print filename
        if filename:
            photos.save(request.files['picture'])
            current_user.image = filename

        db.session.add(current_user)
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit-profile.html', form = form)


@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = user.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        flash('The profile has been updated')
        return redirect(url_for('.user', username = user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit-profile.html', form=form, user=user)


@main.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST' and 'photo' in request.files:
        filename = photos.save(request.files['photo'])
        print filename, "FIELNAME"
        avatar = url_for('static', filename='uploads/{filename}'.format(filename=filename))
        return render_template('upload.html', avatar = avatar)
    return render_template('upload.html')


@main.route('/post/<int:id>', methods=['GET','POST'])
def post(id):
    post = Post.query.get_or_404(id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body = form.body.data, post = post, author=current_user._get_current_object())
        db.session.add(comment)
        flash('Your comment has been published')
        return redirect(url_for('.post', id=post.id, page=-1))
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (post.comments.count() -1)//\
            current_app.config['COMMENTS_PER_PAGE'] + 1
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
        page, per_page=current_app.config['COMMENTS_PER_PAGE'], error_out = False)
    comments = pagination.items                
    return render_template('post.html', posts=[post], form = form,
        comments=comments, pagination=pagination)

@main.route('/comment/<int:id>')
def comment(id):
    comment = Comment.query.filter_by(id = id).first()
    return comment.body, comment.author.username


@main.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    post = Post.query.get_or_404(id)
    if current_user !=post.author and current_user != current_user.can(Permission.ADMINISTER):
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.add(post)
        flash('Post has been updated')
        return redirect(url_for('main.post', id=post.id))
    form.body.data = post.body
    return render_template('edit_post.html', form = form, post=post)

@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user')
        return redirect(url_for('.index'))
    if current_user.is_following(user):
        flash('You are already following this user')
        return redirect(url_for('.user', username=username))
    current_user.follow(user)
    flash('You are now following %s' % username)
    return redirect(url_for('.user', username=username))

@main.route('/user/unfollow')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user')
        return redirect(url_for('.index'))
    if not current_user.is_following(user):
        flash('You dont follow this user')
        return redirect(url_for('.index'))
    if user == current_user:
        return redirect(url_for('.index'))
    current_user.unfollow(user)
    flash('You have unfollowed %s' % user)
    return redirect(url_for('.user', username = user.username))

@main.route('/followers/<username>')
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user')
        return redirect(url_for('.index'))
    page= request.args.get('page', 1, type=int)
    pagination = user.followers.paginate(page, per_page=current_app.config['FOLLOWERS_PER_PAGE'],
                                         error_out = False)
    follows = [{'user': item.follower, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title='Followers of',
                           endpoint ='.followers', pagination=pagination,
                           follows = follows)
@main.route('/followed-by/<username>')
def followed_by(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user')
        return redirect(url_for('.index'))
    page= request.args.get('page', 1, type=int)
    pagination=user.followed.paginate(page, per_page=current_app.config['FOLLOWERS_PER_PAGE'],
                                      error_out=False)
    follows = [{'user': item.followed, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, tile='Followed by',
                           endpoint = '.followed_by', pagination=pagination,
                           follows=follows)

# @app.errorhandler(404)
# def page_not_found(e):
#     print "not found"
#     return render_template('404.html'), 404


# @app.errorhandler(500)
# def internal_server_error(e):
#     return render_template('500.html'), 500
