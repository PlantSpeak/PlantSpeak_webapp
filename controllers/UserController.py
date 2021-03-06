from flask import Blueprint, current_app, url_for, request, redirect, render_template, session, flash
from models.User import *
from models.Notification import *
from database import db
from wtforms import Form, BooleanField, StringField, PasswordField, validators
from wtforms.fields.html5 import EmailField
import flask_bcrypt

user_pages = Blueprint('users', __name__, template_folder="views")

# Forms for user control/related operations.
class LoginForm(Form):
    username = StringField('Username')
    password = PasswordField('Password')

class RegistrationForm(Form):
    username = StringField('Username', [validators.Length(min=USERNAME_MIN_LENGTH, max=USERNAME_MAX_LENGTH)])
    email = EmailField('Email Address', [validators.Length(min=EMAIL_MIN_LENGTH, max=EMAIL_MAX_LENGTH), validators.Email()])
    password = PasswordField('New Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm_password', message='Passwords must match')
    ])
    confirm_password = PasswordField('Repeat Password')

# Checks if user is already in the database.
def userExists(username):
    if User.query.filter_by(username=username).all():
        return True
    return False

# User registration endpoint and processing.
@user_pages.route('/register', methods=['GET','POST'])
def register():
    form = RegistrationForm(request.form)
    if request.method=="POST" and form.validate():
        if not userExists(form.username.data):
            newUser = User(password=form.password.data, username=form.username.data, email=form.email.data, type=0)
            db.session.add(newUser)
            db.session.commit()
            session['user_id'] = newUser.id
            session['username'] = newUser.username
            if newUser.type == 1:
                session['admin'] = True
            else:
                session['admin'] = False
            flash("Your user account has been created!", category="success")
            return redirect(url_for('main.home'))
        else:
            form.username.errors.append("That username is already taken.")
    return render_template("register.html", form=form)

# Flask form for create user page.
class CreateUserForm(Form):
    username = StringField('Username', [validators.Length(min=USERNAME_MIN_LENGTH, max=USERNAME_MAX_LENGTH)])
    email = StringField('Email Address', [validators.Length(min=EMAIL_MIN_LENGTH, max=EMAIL_MAX_LENGTH)])
    admin = BooleanField('Give this user administrator privileges.')

@user_pages.route('/create_user', methods=['GET','POST'])
def create_user():
    if not session.get('user_id'):
        flash("You need to be logged in to do that.", category="danger")
        return redirect(url_for('main.home'))
    user = User.query.filter_by(id=session['user_id']).one()
    if user.type != 1:
        flash("You need administrator priveledges to do that.", category="danger")
        return redirect(url_for('main.home'))
    form = CreateUserForm(request.form)
    random_password = str(uuid.uuid4())[:8]
    if request.method=="POST" and form.validate():
        newUser = User(type=int(form.admin.data), password=random_password, username=form.username.data, email=form.email.data)
        if User.query.filter_by(username=newUser.username).all():
            flash("A user with that username already exists!", category="danger")
        elif User.query.filter_by(email=newUser.email).all():
            flash("A user with that email already exists!", category="danger")
        else:
            db.session.add(newUser)
            db.session.commit()
            registered_notification = Notification(newUser.id, None, "PlantSpeak Registration Details", """You have successfully signed up for PlantSpeak.
             Your login details are as follows:
             USERNAME: %s
             PASSWORD %s""" % (newUser.username, random_password), newUser.email)
            registered_notification.send()
            flash("User created successfully!", category="success")
            return redirect(url_for('main.home'))
    return render_template("create_user.html", form=form)

# Login page.
@user_pages.route('/login', methods=['GET','POST'])
def login():
    if session.get('password_attempts') is None:
        session['password_attempts']=5
    form = LoginForm(request.form)
    if request.method=="POST":
        if session['password_attempts']>0:
            if form.validate():
                user = User.query.filter_by(username=form.username.data).first()
                if user:
                    if user.login(form.password.data):
                        session['password_attempts']=5
                        return redirect(url_for('main.home'))
                    else:
                        session['password_attempts']-=1
                        form.password.errors.append("Incorrect password. %d attempts remaining."%session['password_attempts'])
                        flash("Invalid entries. Please check your entries and try again.", category="danger")
                        return render_template('login.html', form=form)
            flash("Invalid entries. Please check your entries and try again.", category="danger")
            return render_template('login.html', form=form, error="Invalid entries. Please check your entries and try again.")
        else:
            flash("You have exceeded the maximum number of password attempts. Please try again later.", category="danger")
            return render_template('login.html', form=form,
                                   error="You have exceeded the maximum number of password attempts. Please try again later.")
    return render_template('login.html', form=form)

# Logs user out by deleting session cookies.
@user_pages.route('/logout', methods=['GET','POST'])
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('main.home'))

# The following form type and function help render the settings webpage, where users can control
# the types of notifications that they receive.
class SettingsForm(Form):
    push_notifications = BooleanField('Push Notifications')
    email_notifications = BooleanField('Email Notifications')

@user_pages.route('/settings', methods=['GET','POST'])
def settings():
    if not session.get('user_id'):
        flash("You need to be logged in to do that.", category="danger")
        return redirect(url_for('main.home'))

    user = User.query.filter_by(id=session['user_id']).first()
    form = SettingsForm(request.form)

    if request.method=="GET":
        if user.push_notifications == 1:
            form.push_notifications.data = True
        else:
            form.push_notifications.data = False

        if user.email_notifications == 1:
            form.email_notifications.data = True
        else:
            form.email_notifications.data = False

    if request.method=="POST":
        if form.email_notifications.data:
            user.email_notifications = 1
        else:
            user.email_notifications = 0

        if form.push_notifications.data:
            user.push_notifications = 1
        else:
            user.push_notifications = 0
        print(user.push_notifications)
        db.session.commit()
        flash("Your changes to settings have been saved.", category="success")
        return redirect(url_for('main.home'))

    return render_template('settings.html', form=form)



