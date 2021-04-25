from database import bcrypt, db
from flask import current_app

class Reading(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.Integer)
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    light_intensity = db.Column(db.Float)
    soil_moisture = db.Column(db.Float)

    def __init__(self, id, time, temperature, humidity, light_intensity, soil_moisture, moisture_index):
        self.id = id
        self.time = time
        self.temperature = temperature
        self.humidity = humidity
        self.light_intensity = light_intensity
        self.soil_moisture = soil_moisture
        self.moisture_index = moisture_index

    # TODO
    def getMoistureIndex(self):
        return 0

    # TODO
    def getMoistureDescription(self):
        return 0
