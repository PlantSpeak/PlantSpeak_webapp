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
from scheduler_tool import scheduler

from models.Reading import *
from models.Favourite import *

from controllers.UserController import *

from wtforms.form import Form
from wtforms.fields import StringField
from wtforms.validators import DataRequired, MacAddress
from models.Device import *

import paho.mqtt.client as mqtt

from mail_tool import mail

from flask_cors import CORS

# MQTT DETAILS
MQTT_SERVER_ADDRESS = '128.199.252.105' # Change this to your MQTT server address.

# Invisible helper form to help determine whether MAC addresses received are valid.
class MacAdressValidationForm(Form):
    addr = StringField(validators=[DataRequired(), MacAddress()])

# Subscribes to correct channels when connected to MQTT broker.
def on_mqtt_connect(client, userdata, flags, rc):
    client.subscribe('SmartPlant_pairing')
    client.subscribe('SmartPlant')

# Callback to process mqtt message when received via paho.
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
        msg = msg.replace('nan', '"nan"')
        print(msg)
        reading_data = json.loads(msg)

        # If no data for a field, do not save the reading.
        for i in reading_data.keys():
            if reading_data[i] == "nan":
                print("Failed to get complete reading data.")
                return None
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

# NOTIFICATIONS
MESSAGE_MAX_LENGTH = 32768
PHONE_MAX_LENGTH = 16
MAX_TOPIC_LENGTH = 16
SAME_PLANT_NOTIFICATION_COOLDOWN = 3600*4 # 4 Hours between notifications for a single plant.
PUSH_NOTIFICATION_COOLDOWN = 15 # 15 seconds minimum between push notifications.

# Default watering reminder message.
watering_message = """Hey %s,

This is a friendly reminder from PlantSpeak to water your %s, 
located at %s on floor %d.

Regards,
PlantSpeak"""

# Job for APScheduler to regularly run, to remind users to water their plants (where applicable).
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
                                                         plant.level), user.email
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

# Get the time that the last notification for the given favourited plant was sent to the user.
def last_notification(favourite):
    last = Notification.query.filter_by(user_id=favourite.user_id,
                                        plant_id=favourite.plant_id).order_by(Notification.time.desc()).first()
    if last:
        return last.time
    return None

# Send notification to user when environmental conditions deteriorate (according to most recent reading).
def plant_health_alert(plant, plant_problems):
    plant_type = PlantType.query.filter_by(id=plant.type).one()
    for i in Favourite.query.filter_by(plant_id=plant.id).all():
        if i is not None:
            if last_notification(i) is not None:
                if time.time()-last_notification(i) < SAME_PLANT_NOTIFICATION_COOLDOWN:
                    return
            message = "Problems with %s located on level %d, %s:\n"%(plant_type.name, plant.level, plant.location)
            if plant_problems:
                for j in plant_problems.keys():
                    if plant_problems[j]:
                        message+="- %s\n"%j
            user = User.query.filter_by(id=i.user_id).first()
            notification = Notification(i.user_id, plant.id, "A '%s' has problems"%plant_type.name, message, user.email)
            notification.send()
            db.session.add(notification)
            db.session.commit()

# Prepares the scheduler (APScheduler) to send out notifications reminding users to water plants.
def get_watering_reminder_jobs(application):
    with application.app_context():
        for i in Favourite.query.all():
            plant = Plant.query.filter_by(id=i.plant_id).one()
            plant_type = PlantType.query.filter_by(id=plant.type).one()
            if plant_type.requires_water == 1 and plant_type.watering_frequency>0:
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

# Launch Paho client and establish MQTT communications via broker.
def launch_mqtt():
    client = mqtt.Client()
    client.on_connect = on_mqtt_connect
    client.on_message = handle_mqtt_message
    client.connect(MQTT_SERVER_ADDRESS, 1883, 5)
    client.loop_forever()

# Application factory function to prepare all modules and run the application.
def create_app():
    application = Flask(__name__, template_folder="views")
    # This must be set false for emails to actually send.
    application.testing = False

    application.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db" # REPLACE THIS.
    application.secret_key = "VERY SECRET KEY"  # Update for production.

    bcrypt.init_app(application)
    db.init_app(application)
    with application.app_context():
        db.create_all()

    # MAIL SERVER DETAILS
    application.config['MAIL_SERVER'] = 'smtp.gmail.com'
    application.config['MAIL_PORT'] = 465
    application.config['MAIL_USERNAME'] = ''
    application.config['MAIL_PASSWORD'] = ''
    application.config['MAIL_USE_TLS'] = False
    application.config['MAIL_USE_SSL'] = True

    mail.init_app(application)

    watering_reminder_scheduler = get_watering_reminder_jobs(application)

    watering_reminder_scheduler.init_app(application)
    watering_reminder_scheduler.start()

    application.register_blueprint(main_pages)
    application.register_blueprint(user_pages)
    application.register_blueprint(plant_pages)
    application.register_blueprint(api)

    return application

# Run the factory at startup and create separate thread + daemonise mqtt functions
# (otherwise interferes with the smooth operation of the webapp).
application = create_app()
CORS(application)
mqtt_thread = threading.Thread(target=launch_mqtt)
mqtt_thread.setDaemon(True)
mqtt_thread.start()

# Get push notifications (accessed via javascript).
@application.route("/get_notifications", methods=['GET', 'POST'])
def get_push_notifications():
    user = User.query.filter_by(id=session['user_id']).first()
    if user.push_notifications == 1:
        notifications = Notification.query.filter(Notification.time>time.time()-PUSH_NOTIFICATION_COOLDOWN).order_by(Notification.time.desc())
        messages = []
        for i in notifications:
            messages.append(dict(topic=i.topic, message=i.message))
        print(messages)
        return json.dumps(dict(messages=messages))
    return json.dumps(None)

# Prepare the database if it doesn't already exist, and a test user.
@application.before_first_request
def prepare_db():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', type=1, email="admin@plantspeak.com", password='admin')
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    application.run(debug=False, use_reloader=False)
