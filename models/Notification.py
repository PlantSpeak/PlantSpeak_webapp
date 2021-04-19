from flask import current_app
import flask_mail

mail_server = ""
mail_port = ""
admin_email = ""
admin_email_pwd = ""

MESSAGE_MAX_LENGTH = 32768
PHONE_MAX_LENGTH = 16
MAX_TOPIC_LENGTH = 16

current_app.config.update(
	MAIL_SERVER=mail_server,
	MAIL_PORT=mail_port,
	MAIL_USE_SSL=True,
	MAIL_USERNAME = admin_email,
	MAIL_PASSWORD = admin_email_pwd,
    DEBUG=True
)

mail = flask_mail.Mail(current_app)

# As it stands, only email and push notifications are being implemented.
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(MAX_TOPIC_LENGTH))
    message = db.Column(db.String(MESSAGE_MAX_LENGTH))
    email = db.Column(db.String(EMAIL_MAX_LENGTH))
    phone = db.Column(db.String(PHONE_MAX_LENGTH))

    def sendEmail(self):
        msg = flask_mail.Message(self.topic, recipients=[self.email], sender=admin_email)
        msg.body = self.message
        msg.send(self.message)

    def sendSMS(self):
        return

    def send(self):
        if self.email:
            self.sendEmail()

