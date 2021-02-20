from flask import Flask, render_template, request, flash, redirect, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
from flask_mail import Mail
from werkzeug.utils import secure_filename
import os

with open('config.json', 'r') as c:
    params = json.load(c)["params"]
local_server = True

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = params['upload_location']
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=465,
    MAIL_USE_TLS=False,
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['gmail-user'],
    MAIL_PASSWORD=params['gmail-password'],
    SECRET_KEY=b'_5#y2L"F4Q8z\n\xec]/'
)
mail = Mail(app)

if (local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']
db = SQLAlchemy(app)


class Admin(db.Model):
    slno = db.Column(db.Integer, primary_key=True)
    password = db.Column(db.String(20), nullable=False)


class Profile(db.Model):
    slno = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(20), nullable=False)
    profilepic = db.Column(db.String(25), nullable=False)


class Gallery(db.Model):
    slno = db.Column(db.Integer, primary_key=True)
    file = db.Column(db.String(200), nullable=False)
    filename = db.Column(db.String(25), nullable=False)
    category = db.Column(db.String(20), nullable=False)


class Contacts(db.Model):
    slno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), nullable=False)
    sub = db.Column(db.String(20), nullable=False)
    message = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=False)


class Post(db.Model):
    slno = db.Column(db.Integer, primary_key=True)
    badge = db.Column(db.String(20), unique=True, nullable=False)
    title = db.Column(db.String(20), unique=True, nullable=False)
    content = db.Column(db.String(120), nullable=False)
    filename = db.Column(db.String(20), nullable=False)
    img = db.Column(db.String(20), nullable=False)
    date = db.Column(db.String(12), nullable=False)


@app.route("/")
def home():
    row = Profile.query.filter_by().all()
    return render_template('index.html', params=params, profile=row)


@app.route("/gallery")
def gallery():
    gallery = Gallery.query.filter_by().all()
    return render_template('gallery.html', params=params, gallery=gallery)


@app.route("/services")
def services():
    return render_template('services.html', params=params)


@app.route("/blog")
def blog():
    post = Post.query.filter_by().all()
    return render_template('blog.html', params=params, post=post)


@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if (request.method == 'POST'):
        '''Add entry to the database'''
        name = request.form.get('name')
        email = request.form.get('email')
        sub = request.form.get('sub')
        message = request.form.get('message')
        entry = Contacts(name=name, sub=sub, message=message, date=datetime.now(), email=email)
        db.session.add(entry)
        db.session.commit()
        flash("Submitted Successfully")
        mail.send_message("New message from site" + name,
                          sender=email,
                          recipients=params['gmail-user'],
                          body=message)
    return render_template('contact.html', params=params)


@app.route("/login", methods=['GET', 'POST'])
def admin():
    return render_template('login.html', params=params)


@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    contacts = Contacts.query.filter_by().all()
    if 'user' in session and session['user'] == params['admin_user']:
        return render_template('dashboard.html', params=params, contacts=contacts)
    if (request.method == 'POST'):
        row = Admin.query.filter_by(slno=1).first()
        user = request.form.get('username')
        apass = request.form.get('password')
        if (user == params['admin_user'] and apass == row.password):
            session['user'] = user

            return render_template('dashboard.html', params=params, contacts=contacts)
        else:
            flash("Password Not Matched")
    return render_template('login.html', params=params)


@app.route("/galleryupload", methods=['GET', 'POST'])
def galleryupload():
    if 'user' in session and session['user'] == params['admin_user']:
        if (request.method == 'POST'):
            f = request.files['file']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            category = request.form.get('category')
            filename = request.form.get('filename')
            entry = Gallery(file=f.filename, category=category, filename=filename)
            db.session.add(entry)
            db.session.commit()
            flash(" Image Uploaded in Gallery  Successfully")
        return render_template('galleryupload.html', params=params)
    return render_template('login.html', params=params)


@app.route("/profilepic", methods=['GET', 'POST'])
def profilepic():
    if 'user' in session and session['user'] == params['admin_user']:
        if (request.method == 'POST'):
            '''Add entry to the database'''
            filename = request.form.get('filename')
            f = request.files['file']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            row = Profile.query.filter_by(slno=0).first()
            row.filename = filename
            row.profilepic = f.filename
            db.session.commit()
            flash("Profilepic Changed successfully")
        return render_template('profilepic.html', params=params)

    return render_template('login.html', params=params)


@app.route("/posts", methods=['GET', 'POST'])
def posts():
    if 'user' in session and session['user'] == params['admin_user']:

        if (request.method == 'POST'):
            '''Add entry to the database'''
            f = request.files['file']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            title = request.form.get('title')
            badge = request.form.get('badge')
            content = request.form.get('content')
            filename = request.form.get('filename')
            entry = Post(img=f.filename, content=content, badge=badge, filename=filename, title=title,
                         date=datetime.now())
            db.session.add(entry)
            db.session.commit()
            flash("Post Uploaded Successfully")
        post = Post.query.filter_by().all()
        return render_template('posts.html', params=params, post=post)

    return render_template('login.html', params=params)


@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/login')


@app.route("/delete/<slno>")
def delete(slno):
    if 'user' in session and session['user'] == params['admin_user']:
        post = Post.query.filter_by(slno=slno).first()
        db.session.delete(post)
        db.session.commit()
        flash("Deleted Successfully")
    return redirect("/posts")


@app.route("/changepassword", methods=['GET', 'POST'])
def username():
    row = Admin.query.filter_by(slno=1).first()
    if 'user' in session and session['user'] == params['admin_user']:
        if (request.method == 'POST'):
            '''Add entry to the database'''
            npassword = request.form.get('npassword')
            row.password = npassword
            db.session.commit()
            flash("Password Changed  Successfully")
        return render_template('changepassword.html', params=params)
    return render_template('login.html', params=params)


app.run(debug=True)
