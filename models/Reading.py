import datetime
import time

from database import bcrypt, db
from models.Plant import *
from flask import current_app
from datetime import datetime

# This class model contains information the information from
# each set of sensor readings received from the device.
class Reading(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plant_id = db.Column(db.Integer, db.ForeignKey(Plant.id))
    time = db.Column(db.Integer)
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    light_intensity = db.Column(db.Float)
    soil_moisture = db.Column(db.Float)
    mac_address = db.Column(db.String(20))

    def __init__(self, time, plant_id, temperature, humidity, light_intensity, soil_moisture, moisture_index, mac_address):
        self.time = time
        self.temperature = temperature
        self.humidity = humidity
        self.light_intensity = light_intensity
        self.soil_moisture = soil_moisture
        self.moisture_index = moisture_index
        self.mac_address = mac_address
        self.plant_id = plant_id

    @property
    def serialize(self):
        return dict(plant_id=self.plant_id,
                    time=(datetime.fromtimestamp(self.time)).strftime("%D %T"),
                    temperature=self.temperature,
                    humidity=self.humidity,
                    soil_moisture=self.soil_moisture,
                    light_intensity=self.light_intensity)
