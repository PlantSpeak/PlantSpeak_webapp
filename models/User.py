from database import bcrypt, db
from flask import current_app, session
import uuid

# Constants
USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 64
EMAIL_MIN_LENGTH = 6
EMAIL_MAX_LENGTH = 128
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128

# User model/class
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Integer)
    # signed_up = db.Column(db.Time)
    username = db.Column(db.String(USERNAME_MAX_LENGTH), unique=True)
    email = db.Column(db.String(EMAIL_MAX_LENGTH))
    password_hash=db.Column(db.String(256))
    password_salt = db.Column(db.String(36)) # 36 is length of uuid
    push_notifications = db.Column(db.Integer)
    email_notifications = db.Column(db.Integer)
    # last_login = db.Column(db.Time)

    def __init__(self, password, **kwargs):
        super(User, self).__init__(**kwargs)
        self.push_notifications = 1
        self.email_notifications = 1
        # Generate the random salt and then use this when hashing the password.
        self.password_salt = uuid.uuid4().__str__()
        self.password_hash=bcrypt.generate_password_hash(self.password_salt+password)

    def login(self, password_attempt):
        if bcrypt.check_password_hash(self.password_hash, self.password_salt+password_attempt):
            session['user_id'] = self.id
            session['username'] = self.username
            session['admin'] = self.isAdmin()
            return True
        else:
            return False

    def isAdmin(self):
        if self.type==1:
            return True
        return False