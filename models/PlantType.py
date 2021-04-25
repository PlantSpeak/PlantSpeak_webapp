from database import db
import time

PLANT_TYPE_NAME_MAX_LENGTH = 64

class PlantType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(PLANT_TYPE_NAME_MAX_LENGTH), unique=True)
    requires_water = db.Column(db.Integer)
    watering_frequency = db.Column(db.Integer) #Interval in seconds.
    min_temp = db.Column(db.Float)
    max_temp = db.Column(db.Float)
    min_humidity = db.Column(db.Float)
    max_humidity = db.Column(db.Float)
    min_moisture = db.Column(db.Float)
    max_moisture = db.Column(db.Float)
    ideal_moisture_level = db.Column(db.Integer)
    min_light_intensity = db.Column(db.Float)
    max_light_intensity = db.Column(db.Float)
    last_watered = db.Column(db.Integer) # Time in seconds since UNIX epoch.

    def __init__(self, name, requires_water, watering_frequency, min_temp,
                 max_temp, min_humidity, max_humidity, min_moisture, max_moisture,
                 ideal_moisture_level, min_light_intensity, max_light_intensity):
        self.name = name
        self.requires_water = int(requires_water)
        self.watering_frequency = watering_frequency
        self.min_temp = min_temp
        self.max_temp = max_temp
        self.min_humidity = min_humidity
        self.max_humidity = max_humidity
        self.min_moisture = min_moisture
        self.max_moisture = max_moisture
        self.ideal_moisture_level =ideal_moisture_level
        self.min_light_intensity = min_light_intensity
        self.max_light_intensity = max_light_intensity
        self.last_watered = time.time()