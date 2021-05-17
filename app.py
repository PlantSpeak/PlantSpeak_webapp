import datetime
import json
import threading

from flask import Flask, Blueprint, session
from controllers.MainController import main_pages
from controllers.UserController import user_pages
from controllers.PlantController import plant_pages
from controllers.ApiController import api
import flask_sqlalchemy
from database import bcrypt, db
from mqtt_tool import mqtt
from scheduler_tool import scheduler#, watering_reminder_job

from models.Reading import *
from models.Favourite import *

from controllers.UserController import *

from wtforms.form import Form
from wtforms.fields import StringField
from wtforms.validators import DataRequired, MacAddress
from models.Device import *

import paho.mqtt.client as mqtt

from mail_tool import mail

MESSAGE_MAX_LENGTH = 32768
PHONE_MAX_LENGTH = 16
MAX_TOPIC_LENGTH = 16

watering_message = """Hey %s,

This is a friendly reminder from PlantSpeak to water your %s, 
located at %s on floor %d of %s.

Regards,
PlantSpeak"""

def watering_reminder_job(plant_id, user_id):
    with application.app_context():
        plant = Plant.query.filter_by(id=plant_id).one_or_none()
        plant_type = PlantType.query.filter_by(id=plant.type).one_or_none()
        user = User.query.filter_by(id=user_id).one_or_none()
        if plant is not None:
            notification = Notification(user_id, plant_id, "Watering reminder from PlantSpeak",
                                        watering_message %(user.username,
                                                         plant_type.name,
                                                         plant.location,
                                                         plant.level, "site"), user.email
                                                         # plant.site),
                                        )
            db.session.add(notification)
            db.session.commit()
            notification.send()

        favourite= Favourite.query.filter_by(plant_id=plant_id, user_id=user_id).one()
        favourite.last_watering_reminder = time.time()
        db.session.commit()

        if not plant:
            print("Failed to send email for plant %d - plant not found!"%plant_id)
        if not user:
            print("Failed to send email for user %d - user not found!" % user_id)
        if not plant_type:
            print("Failed to send email for plant type %d - plant type not found!" % plant.type)

    print("Sent Email!")

def last_notification(favourite):
    last = Notification.query.filter_by(user_id=favourite.user_id,
                                        plant_id=favourite.plant_id).order_by(Notification.time.desc()).first()
    if last:
        return last.time
    return None


SAME_PLANT_NOTIFICATION_COOLDOWN = 3600*4 # 4 Hours between notifications for a single plant.

def plant_health_alert(plant, plant_problems):
    plant_type = PlantType.query.filter_by(id=plant.type).one()
    for i in Favourite.query.filter_by(plant_id=plant.id).all():
        if i is not None:
            if last_notification(i) is not None:
                if time.time()-last_notification(i)<SAME_PLANT_NOTIFICATION_COOLDOWN:
                    return
            message = "Problems with %s located on level %d, %s:\n"%(plant_type.name,plant.level,plant.location)
            if plant_problems:
                for j in plant_problems.keys():
                    if plant_problems[j]:
                        message+="- %s\n"%j
            user = User.query.filter_by(id=i.user_id).first()
            notification = Notification(i.user_id, plant.id, "A '%s' has problems"%plant_type.name, message, user.email)
            notification.send()
            db.session.add(notification)
            db.session.commit()

class MacAdressValidationForm(Form):
    addr = StringField(validators=[DataRequired(), MacAddress()])


def on_mqtt_connect(client, userdata, flags, rc):
    client.subscribe('SmartPlant_pairing')
    client.subscribe('SmartPlant')

def handle_mqtt_message(client, userdata, message):
    if message.topic == "SmartPlant_pairing":
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
    elif message.topic == "SmartPlant":
        msg = message.payload.decode()
        reading_data = json.loads(msg)
        print(reading_data)
        with application.app_context():
            plant = Plant.query.filter_by(mac_address=reading_data["mac_address"]).one_or_none()
            if plant and Reading.query.filter_by(time=reading_data["time"], mac_address=reading_data["mac_address"]).count()==0:
                reading = Reading(time=reading_data["time"],
                                  plant_id=plant.id,
                                  temperature=reading_data["temp"],
                                  humidity=reading_data["humidity"],
                                  light_intensity=reading_data["light_intensity"],
                                  soil_moisture=reading_data['soil_moisture']*100, # CONVERT TO PERCENTAGE for database.
                                  moisture_index=reading_data["moisture_index"],
                                  mac_address=reading_data["mac_address"])
                plant_health_alert(plant, plant.get_problems(reading))
                db.session.add(reading)
                db.session.commit()
            else:
                print("Similar recording.")

# Prepares the scheduler (APScheduler) to send out notifications reminding users to water plants.
def get_watering_reminder_jobs(application):
    with application.app_context():
        for i in Favourite.query.all():
            plant = Plant.query.filter_by(id=i.plant_id).one()
            plant_type = PlantType.query.filter_by(id=plant.type).one()
            last_watered = i.last_watering_reminder
            if last_watered is not None:
                watering_due = last_watered + plant_type.watering_frequency
                if (time.time() - watering_due) >= plant_type.watering_frequency:
                    scheduler.add_job(id="watering_reminder_plant_%d_user_%d" % (i.plant_id, i.user_id),
                                      args=(i.plant_id, i.user_id),
                                      func=watering_reminder_job, trigger='interval',
                                      seconds=plant_type.watering_frequency,
                                      next_run_time = datetime.fromtimestamp(time.time()), replace_existing=True)
                elif plant_type.watering_frequency > (time.time() - watering_due) > 0:
                    scheduler.add_job(id="watering_reminder_plant_%d_user_%d" % (i.plant_id, i.user_id), args=(i.plant_id, i.user_id),
                                      func=watering_reminder_job, trigger='interval', seconds=plant_type.watering_frequency,
                                      next_run_time=datetime.fromtimestamp(last_watered+plant_type.watering_frequency), replace_existing=True)
                else:
                    scheduler.add_job(id="watering_reminder_plant_%d_user_%d" % (i.plant_id, i.user_id), args=(i.plant_id, i.user_id),
                                      func=watering_reminder_job, trigger='interval', seconds=plant_type.watering_frequency, replace_existing=True)
            scheduler.add_job(id="watering_reminder_plant_%d_user_%d" % (i.plant_id, i.user_id),
                              args=(i.plant_id, i.user_id),
                              func=watering_reminder_job, trigger='interval', seconds=plant_type.watering_frequency, replace_existing=True)
    return scheduler

def launch_mqtt():
    client = mqtt.Client()
    client.on_connect = on_mqtt_connect
    client.on_message = handle_mqtt_message
    client.connect('192.168.1.100', 1883, 5)
    client.loop_forever()

def create_app():
    application = Flask(__name__, template_folder="views")
    # This must be set false for emails to actually send.
    application.testing = True

    application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'  # REPLACE THIS.
    application.secret_key = "VERY SECRET KEY"  # Update for production.

    bcrypt.init_app(application)
    db.init_app(application)
    with application.app_context():
        db.create_all()

    application.config['MAIL_SERVER'] = 'smtp.mailtrap.io'
    application.config['MAIL_PORT'] = 2525
    application.config['MAIL_USERNAME'] = 'a4975278137a6d'
    application.config['MAIL_PASSWORD'] = 'f70fced936ff01'
    application.config['MAIL_USE_TLS'] = True
    application.config['MAIL_USE_SSL'] = False

    mail.init_app(application)

    # application.config['MQTT_BROKER_URL'] = '192.168.1.100'  # use the free broker from HIVEMQ
    # application.config['MQTT_BROKER_PORT'] = 1883  # default port for non-tls connection
    # application.config['MQTT_USERNAME'] = ''  # set the username here if you need authentication for the broker
    # application.config['MQTT_PASSWORD'] = ''  # set the password here if the broker demands authentication
    # application.config['MQTT_KEEPALIVE'] = 5  # set the time interval for sending a ping to the broker to 5 seconds
    # application.config['MQTT_TLS_ENABLED'] = False  # set TLS to disabled for testing purposes
    #
    # mqtt.init_app(application)




    application.config['SCHEDULER_API_ENABLED'] = True

    # application.config['SCHEDULER_JOB_DEFAULTS'] = {"coalesce": False, "standalone": True}
    # application.config['SCHEDULER_EXECUTORS'] = {"default": {"type": "threadpool", "max_workers": 0}}

    watering_reminder_scheduler = get_watering_reminder_jobs(application)

    watering_reminder_scheduler.init_app(application)
    watering_reminder_scheduler.start()

    application.register_blueprint(main_pages)
    application.register_blueprint(user_pages)
    application.register_blueprint(plant_pages)
    application.register_blueprint(api)

    return application


application = create_app()
mqtt_thread = threading.Thread(target=launch_mqtt)
mqtt_thread.setDaemon(True)
mqtt_thread.start()

PUSH_NOTIFICATION_COOLDOWN = 15
@application.route("/get_notifications", methods=['GET', 'POST'])
def get_push_notifications():
    notifications = Notification.query.filter(Notification.time>time.time()-PUSH_NOTIFICATION_COOLDOWN).order_by(Notification.time.desc())
    messages = []
    for i in notifications:
        messages.append(dict(topic=i.topic, message=i.message))
    return json.dumps(dict(messages=messages))

# # FOR DEBUGGING PURPOSES ONLY
# # Remove for production release.
@application.before_first_request
def prepare_db():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', type=1, email="admin@plantspeak.com", password='admin')
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    application.run(debug=True, use_reloader=False)
