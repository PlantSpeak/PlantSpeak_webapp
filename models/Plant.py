from database import db
from models.PlantType import PlantType

# Constants
NAME_MIN_LENGTH = 2
NAME_MAX_LENGTH = 128
LOCATION_MIN_LENGTH = 1 # Use '-' for empty locations/field?
LOCATION_MAX_LENGTH = 64
PLANT_ID_LENGTH = 16

# A model to manage information about a plant after it is added to the system.
class Plant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plant_id = db.Column(db.String(PLANT_ID_LENGTH))
    type = db.Column(db.Integer)
    level = db.Column(db.Integer)
    location = db.Column(db.String(LOCATION_MAX_LENGTH))
    mac_address = db.Column(db.String)

    def __init__(self, **kwargs):
        super(Plant, self).__init__(**kwargs)

#   The functions below check the plant sensor readings against user-defined
#   thresholds for each plant type.

    def temperature_too_low(self, reading, plant_type):
        if plant_type.max_temp:
            if reading.temperature<plant_type.min_temp:
                return True
        return False

    def temperature_too_high(self, reading, plant_type):
        if plant_type.max_temp:
            if reading.temperature>plant_type.max_temp:
                return True
        return False

    def humidity_too_low(self, reading, plant_type):
        if plant_type.min_humidity:
            if reading.humidity<plant_type.min_humidity:
                return True
        return False

    def humidity_too_high(self, reading, plant_type):
        if plant_type.max_humidity:
            if reading.humidity>plant_type.max_humidity:
                return True
        return False

    def soil_moisture_too_low(self, reading, plant_type):
        if plant_type.min_moisture:
            if reading.soil_moisture<plant_type.min_moisture:
                return True
        return False

    def soil_moisture_too_high(self, reading, plant_type):
        if plant_type.max_moisture:
            if reading.soil_moisture>plant_type.max_moisture:
                return True
        return False

    def light_intensity_too_low(self, reading, plant_type):
        if plant_type.min_light_intensity:
            if reading.light_intensity<plant_type.min_light_intensity:
                return True
        return False

    def light_intensity_too_high(self, reading, plant_type):
        if plant_type.max_light_intensity:
            if reading.light_intensity>plant_type.max_light_intensity:
                return True
        return False

#   This function returns a dictionary containing details about which plant
#   environmental thresholds have been exceeded for a given reading.
    def get_problems(self, reading):
        plant_type = PlantType.query.filter_by(id=self.type).one()
        problems = dict(temperature_low=self.temperature_too_low(reading, plant_type),
                        temperature_high=self.temperature_too_high(reading, plant_type),
                        humidity_low=self.humidity_too_low(reading, plant_type),
                        humidity_high=self.humidity_too_high(reading, plant_type),
                        moisture_low=self.soil_moisture_too_low(reading, plant_type),
                        moisture_high=self.soil_moisture_too_high(reading, plant_type),
                        light_intensity_low=self.light_intensity_too_low(reading, plant_type),
                        light_intensity_high=self.light_intensity_too_high(reading, plant_type))
        return problems