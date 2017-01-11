# not covered in book https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xiv-i18n-and-l10n
from . import main
from ..mail import send_mail
from flask import render_template, flash, redirect, request, abort, url_for, current_app, make_response, g
from datetime import datetime
from ..models import User, Role, Permission, Post, Comment, Knjige, Source
from flask_login import login_required, current_user
from forms import EditProfileForm, EditProfileAdminForm, PostForm, CommentForm, SearchForm
from ..  import db
from ..decorators import admin_required, permission_required
from .. import photos
from werkzeug.utils import secure_filename
import  os
#from config import MAX_SEARCH_RESULTS
MAX_SEARCH_RESULTS = 50



@main.route('/', methods=['GET', 'POST'])
@main.route('/index', methods=['GET', 'POST'])
def index():
    #post_form = PostForm()
    search_form = SearchForm()
    #
    # if current_user.can(Permission.WRITE_ARTICLES) and post_form.validate_on_submit():
    #     print "HIT"
    #     post = Post(body = post_form.body.data, author=current_user._get_current_object(), timestamp=datetime.utcnow())
    #     db.session.add(post)
    #     db.session.commit()
    #     return redirect(url_for('.index'))
    #posts = Post.query.order_by(Post.timestamp.desc()).all()
#pagination = Post.query.order_by(Post.timestamp.desc()).paginate(page, per_page=current_app.config['POSTS_PER_PAGE'],
                                                                     # error_out=False)
    #posts = pagination.items

    # show_followed = False
    # page = request.args.get('page', 1, type=int)
    # if current_user.is_authenticated:
    #     show_followed = bool(request.cookies.get('show_followed', ''))
    # if show_followed:
    #     query=current_user.followed_posts
    # else:
    #     query = Post.query
    # pagination =  query.order_by(Post.timestamp.desc()).paginate(
    #     page, per_page=current_app.config['POSTS_PER_PAGE'], error_out=False)
    # posts = pagination.items

    return render_template("index.html", search_form=search_form, current_time=datetime.utcnow())




@main.route('/all')
@login_required
def show_all():
    resp = make_response(redirect(request.referrer))
    resp.set_cookie('show_followed', '', max_age=30*24*60*60)
    return resp


@main.route('/followed')
@login_required
def show_followed():
    resp = make_response(redirect(request.referrer))
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
    pagination = post.comments.filter_by(parrent_id=None).order_by(Comment.timestamp.asc()).paginate(
        page, per_page=current_app.config['COMMENTS_PER_PAGE'], error_out = False)
    comments = pagination.items                
    return render_template('post.html', posts=[post], post_form = form,
        comments=comments, pagination=pagination, Comment=Comment)

@main.route('/comment/<int:id>', methods=['POST','GET'])
@login_required
def comment(id):
    parrent_comment = Comment.query.filter_by(id = id).first()
    post = Post.query.filter_by(id=parrent_comment.post_id).first()
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data, post=post, author = current_user._get_current_object(), parrent_id=parrent_comment.id)
        db.session.add(comment)
        flash('Your comment has been added')
        return redirect(url_for('.post', id=post.id))

    return render_template('comments.html', form=form, parrent = parrent_comment, Comment=Comment)


@main.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author and not current_user.can(Permission.ADMINISTER):
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.add(post)
        flash('Post has been updated')
        return redirect(url_for('main.post', id=post.id))
    form.body.data = post.body
    return render_template('edit_post.html', form = form, post=post)

@main.route('/follow/<type>/<name>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(type, name):
    print type, name
    if type == 'User':
        user = User.query.filter_by(username=name).first()
        if user is None:
            flash('Invalid user')
            return redirect(url_for('.index'))
        if current_user.is_following(user, type):
            flash('You are already following this user')
            return redirect(url_for('.user', username=name))
        current_user.follow(user, type)
        flash('You are now following %s' % name)
    elif type == 'naziv' or type =='autor' or type == 'genre':
        print "ELSE"

        kwargs = {type : name}
        item = Knjige.query.filter_by(**kwargs).first()
        print "ITEM is ", item
        if item is None:
            flash('invalid %s'), type
            return redirect(request.referrer)
        if  current_user.is_following(item, 'item'):
            print "True"
            flash('You are already following this user')
            return redirect(request.referrer)
        current_user.follow(item, 'item')
        flash('You are now following %s' % name)
    print "REQUEST REFFERER IS ", request.referrer
    return redirect(request.referrer)

@main.route('/unfollow/<type>/<name>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(type, name):
    if type == 'book':
        user = User.query.filter_by(username=name).first()
        if user is None:
            flash('Invalid user')
            return redirect(url_for('.index'))
        if not current_user.is_following(user, type):
            flash('You dont follow this user')
            return redirect(url_for('.index'))
        if user == current_user:
            return redirect(url_for('.index'))
        current_user.unfollow(user, type)
        flash('You have unfollowed %s' % user)

    elif type =='naziv' or type == 'Autor' or type =='Genre':
        print "Unfollow"
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

@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate():
    show_disabled = bool(request.cookies.get('show_disabled', ''))
    if show_disabled:
        query = Comment.query.filter_by(disabled=True)

    else:
        query = Comment.query    
    page = request.args.get('page', 1, type=int)
    pagination = query.order_by(Comment.timestamp.desc()).paginate(page, per_page=current_app.config['COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('moderate.html', comments=comments, pagination=pagination, page=page, Comment=Comment, show_disabled=show_disabled)


@main.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_enable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    db.session.add(comment) 
    return redirect(url_for('.moderate', page=request.args.get('page', 1, type=int)))


@main.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_disable(id):
    print 'moderate disable'
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    db.session.add(comment)
    return redirect(url_for('.moderate', page=request.args.get('page', 1, type=int)))


@main.route('/moderate/show_disabled')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_disabled():
    """Shows only disabled comments to mod panel"""
    resp = make_response(redirect(url_for('.moderate')))
    resp.set_cookie('show_disabled', '1', max_age= 30*24*60*60)
    return resp

@main.route('/moderate/show_all')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_all():
    """Shows all comments to mod panel"""
    resp = make_response(redirect(url_for('.moderate')))
    resp.set_cookie('show_disabled', '', max_age = 30*24*60*60)
    return resp

@main.route('/search', methods=['POST'])
def search():
    search_form = SearchForm()
    if not search_form.validate_on_submit():
        return redirect(url_for('.index'))
    return redirect(url_for('.search_result',query = search_form.search.data))    

@main.route('/search_results/<query>')    
def search_result(query):
    search = True
    results= Knjige.query.whoosh_search(query, MAX_SEARCH_RESULTS).all()
    print results
    return render_template('search_results.html', query=query, results=results, search=search)

@main.route('/book_page/<book_id>', methods = ['POST', 'GET'])
def book_page(book_id):
    post_form = PostForm()
    book = Knjige.query.filter_by(id=book_id).first()
    if book:
        book_title= book.naziv
        book_autor = book.autor
        posts = Post.query.filter_by(book_id = book_id).all()
        source = Source.query.filter_by(knjiga = book_id).all()
        autor_books = Knjige.query.filter_by(autor = book_autor).all()
        if current_user.can(Permission.WRITE_ARTICLES) and post_form.validate_on_submit():
            post = Post(body = post_form.body.data, book_id = book_id, author = current_user._get_current_object(),
                        timestamp = datetime.utcnow())
            db.session.add(post)
            db.session.commit()
            return redirect(url_for('.book_page', book_id=book_id))
        return render_template('book_page.html', book_title = book_title, book_autor= book_autor, source=source,
                               autor_books=autor_books, posts=posts, post_form=post_form, item = book)
    else:
        abort(404)

@main.route('/dashboard/<username>')
@login_required
def dashboard(username):
    items = None
    show_followed = False
    # page = request.args.get('page', 1, type=int)
    # if current_user.is_authenticated:
    show_followed = bool(request.cookies.get('show_followed', ''))
    if show_followed:
        query = current_user.followed_posts
        items = current_user.followed_items #.order_by(Post.timestamp.desc())
        posts = query.union(items).order_by(Post.timestamp.desc())

    else:
        posts = Post.query.order_by(Post.timestamp.desc())
    # pagination = query.order_by(Post.timestamp.desc()).paginate(
        # page, per_page=current_app.config['POSTS_PER_PAGE'], error_out=False)

    return render_template('dashboard.html', posts=posts,  show_followed=show_followed, username=username)



        
# @app.errorhandler(40Permissio4)
# def page_not_found(e):
#     print "not found"
#     return render_template('404.html'), 404


# @app.errorhandler(500)
# def internal_server_error(e):
#     return render_template('500.html'), .add500
