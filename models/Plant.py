from database import bcrypt, db
from flask import current_app
import uuid

NAME_MIN_LENGTH = 2
NAME_MAX_LENGTH = 128
LEVEL_MIN_LENGTH = 1
LEVEL_MAX_LENGTH = 64
LOCATION_MIN_LENGTH = 1 # Use '-' for empty locations/field?
LOCATION_MAX_LENGTH = 64


class Plant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Integer)

    level = db.Column(db.Integer)
    location = db.Column(db.String(LOCATION_MAX_LENGTH))


    def __init__(self, **kwargs):
        super(Plant, self).__init__(**kwargs)
        #self.level = 0
        #self.location = '-'
