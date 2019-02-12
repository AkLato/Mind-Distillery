import os, random, csv
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request
from minddis import app, db, bcrypt
from minddis.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm, CommentForm
from minddis.models import User, Post, Comment, Post_Comment
from flask_login import login_user, current_user, logout_user, login_required


@app.route("/")
@app.route("/home")
def home():
    
    r_quote = random_quote()
    r = random_bg()
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=3)
    return render_template('home.html', posts=posts, r=r, r_quote=r_quote)


@app.route("/about")
def about():
    
    r_quote = random_quote()
    r = random_bg()
    return render_template('about.html', title='About', r=r, r_quote=r_quote)


@app.route("/register", methods=['GET', 'POST'])
def register():
    
    r_quote = random_quote()
    r = random_bg()
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Účet vytvořen pro {form.username.data}!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form, r=r, r_quote=r_quote)


@app.route("/login", methods=['GET', 'POST'])
def login():
    
    r_quote = random_quote()
    r = random_bg()
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Přihlášení se nepovedlo, zkontrolujte zadané údaje.')
    return render_template('login.html', title='Login', form=form, r=r, r_quote=r_quote)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (128, 128)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    
    r_quote = random_quote()
    r = random_bg()
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.motto = form.motto.data
        db.session.commit()
        flash('Your account has been updated!')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.motto.data = current_user.motto
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account', image_file=image_file,
                            form=form, r=r, r_quote=r_quote)

@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    
    r_quote = random_quote()
    r = random_bg()
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post',
                           form=form, legend='New Post', r=r, r_quote=r_quote)

@app.route("/post/<int:post_id>", methods=['GET', 'POST'])
def post(post_id):
    form = CommentForm()
    r_quote = random_quote()
    r = random_bg()
    post = Post.query.get_or_404(post_id)
    post_comments = Post_Comment.query.order_by(Post_Comment.date_posted.desc())
    if form.validate_on_submit():
        post_comment = Post_Comment(username=form.username.data, content=form.content.data)
        db.session.add(post_comment)
        db.session.commit()
        flash('Comment added.')
    return render_template('post.html', title=post.title, post=post, r=r, r_quote=r_quote, 
                                        form=form, post_comments=post_comments)

@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    
    r_quote = random_quote()
    r = random_bg()
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update Post',
                           form=form, legend='Update Post', r=r, r_quote=r_quote)


@app.route("/post/<int:post_id>/delete", methods=['GET','POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!')
    return redirect(url_for('home'))

@app.route("/user/<string:username>")
def user_posts(username):
    
    r_quote = random_quote()
    r = random_bg()
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user)\
        .order_by(Post.date_posted.desc())\
        .paginate(page=page, per_page=5)
    return render_template('user_posts.html', posts=posts, user=user, r=r, r_quote=r_quote)

@app.route("/post/<int:post_id>/post_comment", methods=['GET', 'POST'])
def post_comment():
  
    post_comments = Post_Comment.query.order_by(Post_Comment.date_posted.desc())
    form = CommentForm()
    if form.validate_on_submit():
        post_comment = Post_Comment(username=form.username.data, content=form.content.data)
        db.session.add(post_comment)
        db.session.commit()
        flash('Comment added.')
        return redirect(url_for('/post/<int:post_id>/'))
    return render_template('/post/<int:post_id>/', title='Comment', form=form, r=r,
                           r_quote=r_quote, post_comments=post_comments)

@app.route("/comments", methods=['GET', 'POST'])
def comments():
  
    r_quote = random_quote()
    r = random_bg()
    comments = Comment.query.order_by(Comment.date_posted.desc())
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(username=form.username.data, content=form.content.data)
        db.session.add(comment)
        db.session.commit()
        flash('Comment added.')
        return redirect(url_for('comments'))
    return render_template('comments.html', title='Comment', r=r,
                           r_quote=r_quote, comments=comments, form=form)


def random_bg():
    r = random.choice(os.listdir(os.path.join(app.static_folder, 'backgrounds')))
  
    return r


def random_quote():
    quote = [
'Blogging is still cool. Now in Flask!',
'Something something.',
'Such randomness, much wow.',
"It's either pretty or functional.",
'You can observe a lot by just watching.',
'It’s like déja vu all over again.',
'No one goes there nowadays, it’s too crowded.',
'Always go to other people’s funerals, otherwise they won’t come to yours.',
'I usually take a two-hour nap from one to four.',
'Never answer an anonymous letter.',
'Pair up in threes.',
'You’ve got to be very careful if you don’t know where you are going, because you might not get there.',
'It was impossible to get a conversation going, everybody was talking too much.',
'I never said most of the things I said.',
'If you ask me anything I don’t know, I’m not going to answer.',
'A rational person can find peace by cultivating indifference to things outside of their control.',
'People spend too much time doing and not enough time thinking about what they should be doing.',
'If it entertains you now but will bore you someday, it’s a distraction. Keep looking.',
'If the primary purpose of school was education, the Internet should obsolete it. But school is mainly about credentialing.',
'Desire is a contract that you make with yourself to be unhappy until you get what you want.',
'Who you do business with is just as important as what you choose to do.',
'If you can’t see yourself working with someone for life, don’t work with them for a day.',
'Earn with your mind, not your time.',
'The older the problem, the older the solution.',
'If they can train you to do it, then eventually they will train a computer to do it.',
'To be honest, speak without identity.',
'Truth is that which has predictive power.',
'Competing without software is like competing without electricity.',
]

    return random.choice(quote)