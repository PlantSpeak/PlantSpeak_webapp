from flask import Blueprint, current_app, url_for, request, redirect, render_template, session
from models.User import *
from models.Notification import *
from database import db
from wtforms import Form, BooleanField, StringField, PasswordField, validators
import flask_bcrypt

user_pages = Blueprint('users', __name__, template_folder="views")

class RegistrationForm(Form):
    username = StringField('Username', [validators.Length(min=USERNAME_MIN_LENGTH, max=USERNAME_MAX_LENGTH)])
    email = StringField('Email Address', [validators.Length(min=EMAIL_MIN_LENGTH, max=EMAIL_MAX_LENGTH)])
    password = PasswordField('New Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm_password', message='Passwords must match')
    ])
    confirm_password = PasswordField('Repeat Password')

@user_pages.route('/register', methods=['GET','POST'])
def register():
    form = RegistrationForm(request.form)
    if request.method=="POST" and form.validate():
        newUser = User(password=form.password.data, username=form.username.data, email=form.email.data)
        db.session.add(newUser)
        db.session.commit()
        session['username'] = newUser.username
        return redirect(url_for('home'))
    return render_template("register.html", form=form)

class CreateUserForm(Form):
    username = StringField('Username', [validators.Length(min=USERNAME_MIN_LENGTH, max=USERNAME_MAX_LENGTH)])
    email = StringField('Email Address', [validators.Length(min=EMAIL_MIN_LENGTH, max=EMAIL_MAX_LENGTH)])

@user_pages.route('/create_user', methods=['GET','POST'])
def create_user():
    form = CreateUserForm(request.form)
    random_password = str(uuid.uuid4())[:8]
    if request.method=="POST" and form.validate():
        newUser = User(password=random_password, username=form.username.data, email=form.email.data)
        db.session.add(newUser)
        db.session.commit()
        registered_notification = Notification("PlantSpeak Registration Details", """You have successfully signed up for PlantSpeak.
         Your login details are as follows:
         USERNAME: %s
         PASSWORD %s""" % (newUser.username, random_password), newUser.email)
        registered_notification.sendEmail()
        return redirect(url_for('home'))
    return render_template("create_user.html", form=form)