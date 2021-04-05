from flask import Blueprint, current_app, url_for, request, redirect, render_template, session
from models.User import *
from database import db
from wtforms import Form, BooleanField, StringField, PasswordField, validators
import flask_bcrypt

plant_pages = Blueprint('users', __name__, template_folder="views")

class RegistrationForm(Form):
    plantname = StringField('Plant Name', [validators.Length(min=NAME_MIN_LENGTH, max=NAME_MAX_LENGTH)])
    email = StringField('Email Address', [validators.Length(min=EMAIL_MIN_LENGTH, max=EMAIL_MAX_LENGTH)])
    password = PasswordField('New Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm_password', message='Passwords must match')
    ])
    confirm_password = PasswordField('Repeat Password')

@plant_pages.route('/register/plant', methods=['GET','POST'])
def register():
    form = RegistrationForm(request.form)
    if request.method=="POST" and form.validate():
        newUser = User(password=form.password.data, username=form.username.data, email=form.email.data)
        db.session.add(newUser)
        db.session.commit()
        session['username'] = newUser.username
        return redirect(url_for('home'))
    return render_template("register.html", form=form)