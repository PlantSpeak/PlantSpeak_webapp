from flask import Flask, Blueprint, session
from controllers.MainController import main_pages
from controllers.UserController import user_pages
from controllers.PlantController import plant_pages
import flask_sqlalchemy
from database import bcrypt, db
from mail_tool import mail

from controllers.UserController import *

MESSAGE_MAX_LENGTH = 32768
PHONE_MAX_LENGTH = 16
MAX_TOPIC_LENGTH = 16

def create_app():
    application = Flask(__name__, template_folder="views")
    application.testing = True

    application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'  # REPLACE THIS.
    application.secret_key = "VERY SECRET KEY"  # Update for production.

    bcrypt.init_app(application)
    db.init_app(application)

    application.config['MAIL_SERVER'] = 'smtp.mailtrap.io'
    application.config['MAIL_PORT'] = 2525
    application.config['MAIL_USERNAME'] = '06f82b5867a132'
    application.config['MAIL_PASSWORD'] = '1fb024fddad45a'
    application.config['MAIL_USE_TLS'] = True
    application.config['MAIL_USE_SSL'] = False

    mail.init_app(application)

    application.register_blueprint(main_pages)
    application.register_blueprint(user_pages)
    application.register_blueprint(plant_pages)

    return application

application = create_app()

# FOR DEBUGGING PURPOSES ONLY
# Remove for production release.
@application.before_first_request
def prepare_db():
    db.create_all()

if __name__ == '__main__':
    application.run(debug=True, use_reloader=True)
