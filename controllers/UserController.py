from flask import Blueprint, current_app, url_for, request, redirect, render_template, session
from models.User import *
from database import db
from wtforms import Form, BooleanField, StringField, PasswordField, validators
import flask_bcrypt

user_pages = Blueprint('users', __name__, template_folder="views")

class LoginForm(Form):
    username = StringField('Username')
    password = PasswordField('Password')

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
        return redirect(url_for('main.home'))
    return render_template("register.html", form=form)

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
                        return redirect(url_for('main.home'))
                    else:
                        session['password_attempts']-=1
                        form.password.errors.append("Incorrect password. %d attempts remaining."%session['password_attempts'])
                        return render_template('login.html', form=form)
            return render_template('login.html', form=form, error="Invalid entries. Please check your entries and try again.")
        else:
            return render_template('login.html', form=form,
                                   error="You have exceeded the maximum number of password attempts. Please try again later.")
    return render_template('login.html', form=form)

@user_pages.route('/logout', methods=['GET','POST'])
def logout():
    session.pop('username')
    return redirect(url_for('main.home'))