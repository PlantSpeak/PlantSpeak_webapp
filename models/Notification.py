from flask import current_app
from database import bcrypt, db
from mail_tool import mail
from flask_mail import Message

MESSAGE_MAX_LENGTH = 32768
PHONE_MAX_LENGTH = 16
MAX_TOPIC_LENGTH = 16
EMAIL_MAX_LENGTH = 256

# As it stands, only email and push notifications are being implemented.
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(MAX_TOPIC_LENGTH))
    message = db.Column(db.String(MESSAGE_MAX_LENGTH))
    email = db.Column(db.String(EMAIL_MAX_LENGTH))

    def __init__(self, topic, message, email):
        self.topic = topic
        self.message = message
        self.email = email

    def sendEmail(self):
        msg = Message(self.topic, recipients=[self.email], sender='PlantSpeak')
        msg.body = self.message
        mail.send(msg)

    def sendSMS(self):
        return

    def send(self):
        if self.email:
            self.sendEmail()

