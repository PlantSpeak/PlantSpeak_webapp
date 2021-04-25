from flask import Flask, Blueprint, session
from controllers.UserController import user_pages
from controllers.PlantController import plant_pages
import flask_sqlalchemy
from database import bcrypt, db

from controllers.UserController import *

def create_app():
    application = Flask(__name__, template_folder="views")

    application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'  # REPLACE THIS.
    application.secret_key = "VERY SECRET KEY"  # Update for production.

    bcrypt.init_app(application)
    db.init_app(application)

    application.register_blueprint(user_pages)
    application.register_blueprint(plant_pages)
    return application

application = create_app()

# FOR DEBUGGING PURPOSES ONLY
# Remove for production release.
@application.before_first_request
def prepare_db():
    db.create_all()

@application.route('/')
def home():
    if session.get('username'):
        return 'Welcome to PlantSpeak, %s!' % session['username']
    return 'Welcome to PlantSpeak!'

if __name__ == '__main__':
    application.run(debug=True, use_reloader=True)

