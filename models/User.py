from app import db, bcrypt, session
import uuid

USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 64
EMAIL_MIN_LENGTH = 6
EMAIL_MAX_LENGTH = 128
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Integer)
    # signed_up = db.Column(db.Time)
    username = db.Column(db.String(USERNAME_MAX_LENGTH))
    email = db.Column(db.String(EMAIL_MAX_LENGTH))
    password_hash=db.Column(db.String(256))
    password_salt = db.Column(db.String(36)) # 36 is length of uuid
    # last_login = db.Column(db.Time)

    def __init__(self, password, **kwargs):
        super(User, self).__init__(**kwargs)
        self.password_salt = uuid.uuid4().__str__()
        self.password_hash=bcrypt.generate_password_hash(self.password_salt+password)

    def login(self, password_attempt):
        if bcrypt.check_password_hash(self.password_hash, self.password_salt+password_attempt):
            session['username'] = self.username
            return True
        else:
            return False

    def logout(self):
        session.pop('username', None)