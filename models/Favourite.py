from database import db
from models.Plant import *
from models.User import *
import time

class Favourite(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), primary_key=True)
    plant_id = db.Column(db.Integer, db.ForeignKey(Plant.id), primary_key=True)
    last_watering_reminder = db.Column(db.Integer)

    def __init__(self, user_id, plant_id):
        self.user_id = user_id
        self.plant_id = plant_id