from flask import Flask, Blueprint, session
from controllers.MainController import main_pages
from controllers.UserController import user_pages
from controllers.PlantController import plant_pages
import flask_sqlalchemy
from database import bcrypt, db
from mail_tool import mail
from mqtt_tool import mqtt

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

    application.config['MQTT_BROKER_URL'] = '192.168.1.100'  # use the free broker from HIVEMQ
    application.config['MQTT_BROKER_PORT'] = 1883  # default port for non-tls connection
    application.config['MQTT_USERNAME'] = ''  # set the username here if you need authentication for the broker
    application.config['MQTT_PASSWORD'] = ''  # set the password here if the broker demands authentication
    application.config['MQTT_KEEPALIVE'] = 5  # set the time interval for sending a ping to the broker to 5 seconds
    application.config['MQTT_TLS_ENABLED'] = False  # set TLS to disabled for testing purposes

    mqtt.init_app(application)

    application.register_blueprint(main_pages)
    application.register_blueprint(user_pages)
    application.register_blueprint(plant_pages)

    return application



from mqtt_tool import mqtt
from wtforms.form import Form
from wtforms.fields import StringField
from wtforms.validators import DataRequired, MacAddress
from models.Device import *


application = create_app()


# FOR DEBUGGING PURPOSES ONLY
# Remove for production release.
@application.before_first_request
def prepare_db():
    db.create_all()
    admin = User(username='admin', type=1, email="admin@plantspeak.com", password='admin')
    db.session.add(admin)
    db.session.commit()
class MacAdressValidationForm(Form):
    addr = StringField(validators=[DataRequired(), MacAddress()])

@mqtt.on_connect()
def on_mqtt_connect(client, userdata, flags, rc):
    mqtt.subscribe('test')

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    msg = message.payload.decode()
    print(msg)
    macform = MacAdressValidationForm()
    macform.addr.data = msg
    if macform.validate():
        with application.app_context():
            found = Device.query.filter_by(mac_address=msg).first()
            if not found:
                device = Device(msg, time.time())
                db.session.add(device)
            else:
                found.last_seen = time.time()
            db.session.commit()



if __name__ == '__main__':
    application.run(debug=True, use_reloader=True)
