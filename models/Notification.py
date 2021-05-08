from flask import current_app
from database import bcrypt, db
from mail_tool import mail
from flask_mail import Message
import time

NOTIFICATION_COOLDOWN = 1800 # 30 Minutes between notifications. Notifications in this time range will be concatenated into a single message.
MESSAGE_MAX_LENGTH = 32768
PHONE_MAX_LENGTH = 16
MAX_TOPIC_LENGTH = 16
EMAIL_MAX_LENGTH = 256

types = {0: "Watering Reminder",
         1: "Plant Health Problems"}

# As it stands, only email and push notifications are being implemented.
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Integer)
    user_id = db.Column(db.Integer)
    plant_id = db.Column(db.Integer)
    topic = db.Column(db.String(MAX_TOPIC_LENGTH))
    message = db.Column(db.String(MESSAGE_MAX_LENGTH))
    email = db.Column(db.String(EMAIL_MAX_LENGTH))
    time = db.Column(db.Integer)

    def __init__(self, user_id, plant_id, topic, message, email):
        self.user_id = user_id
        self.plant_id = plant_id
        self.topic = topic
        self.message = message
        self.email = email
        self.time = time.time()

    def sendEmail(self):
        msg = Message(self.topic, recipients=[self.email], sender='PlantSpeak')
        msg.body = self.message
        mail.send(msg)

    def send(self):
        if self.email:
            self.sendEmail()

