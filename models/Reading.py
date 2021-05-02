from database import bcrypt, db
from models.Plant import *
from flask import current_app

class Reading(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plant_id = db.Column(db.Integer, db.ForeignKey(Plant.id))
    time = db.Column(db.Integer)
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    light_intensity = db.Column(db.Float)
    soil_moisture = db.Column(db.Float)
    mac_address = db.Column(db.String(20))

    def __init__(self, time, temperature, humidity, light_intensity, soil_moisture, moisture_index, mac_address):
        self.time = time
        self.temperature = temperature
        self.humidity = humidity
        self.light_intensity = light_intensity
        self.soil_moisture = soil_moisture
        self.moisture_index = moisture_index
        self.mac_address = mac_address

    # TODO
    def getMoistureIndex(self):
        return 0

    # TODO
    def getMoistureDescription(self):
        return 0
