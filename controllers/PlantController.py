from flask import Blueprint, current_app, url_for, request, redirect, render_template, session
from models.Plant import *
from database import db
from wtforms import Form, BooleanField, StringField, PasswordField, validators
import flask_bcrypt

plant_pages = Blueprint('plants', __name__, template_folder="views")

class RegistrationForm(Form):
    #plantname = StringField('Plant Name', [validators.Length(min=NAME_MIN_LENGTH, max=NAME_MAX_LENGTH)])
    level = StringField('Plant Level', [validators.Length(min=LEVEL_MIN_LENGTH, max=LEVEL_MAX_LENGTH)])
    location = StringField('Plant Location', [validators.Length(min=LOCATION_MIN_LENGTH, max=LOCATION_MAX_LENGTH)])


@plant_pages.route('/register/plant', methods=['GET','POST'])
def register():
    form = RegistrationForm(request.form)
    if request.method=="POST" and form.validate():
        newPlant = Plant(level =  form.level.data, location=form.location.data)
        db.session.add(newPlant)
        db.session.commit()
        #session['username'] = newUser.username
        return redirect(url_for('home'))
    return render_template("register.html", form=form)