from flask import Blueprint, request, jsonify
from models.Reading import *
import json

api = Blueprint('api', __name__)

# RESTful API
#   The following RESTful API endpoints allow for the manipulation of reading entries in the database.
#
#   Requests for all endpoints except GET (which takes plant id as a parameter in the GET request)
#   should have json as the body content in the following format:
#   { "id": <only required if updating existing reading>,
#       "mac_address": <the mac address of the device you are making the reading for>,
#       "temperature": <ambient temperature percentage>,
#       "humidity": <ambient humidity percentage>,
#       "soil_moisture": <volumetric soil moisture %>,
#       "light_intensity": <light intensity of reading in lux>
#   }

# GET existing reading in the database.
@api.route('/api/readings', methods=['GET'])
def get_readings():
    id = request.args.get('id')
    num_readings = request.args.get('num_readings')
    return jsonify([i.serialize for i in Reading.query.filter_by(plant_id=id).order_by(Reading.time.desc()).limit(num_readings).all()])

# POST or write a new reading to the database.
@api.route('/api/readings', methods=['POST'])
def add_reading():
    response = {"errors": None}
    reading = json.loads(request.data)
    try:
        mac_addr = reading["mac_address"]
    except KeyError:
        response["errors"] = "Please provide a valid mac address."
    print(reading)
    temperature = float(reading["temperature"])
    humidity = float(reading["humidity"])
    light_intensity = float(reading["light_intensity"])
    soil_moisture = float(reading["soil_moisture"])
    if mac_addr is not None:
        plant = Plant.query.filter_by(mac_address=mac_addr).first()
        reading = Reading(time=time.time(), plant_id=plant.id, temperature=temperature, humidity=humidity,
                          light_intensity=light_intensity, soil_moisture=soil_moisture, mac_address=mac_addr, moisture_index=None)
        db.session.add(reading)
        db.session.commit()
    return response

# PATCH or update an existing reading in the database.
@api.route('/api/readings', methods=['PATCH'])
def update_reading():
    response = {"errors": None}
    reading = json.loads(request.data)
    existing_record = Reading.query.filter_by(id=reading["id"]).one()
    if reading["temperature"]:
        existing_record.temperature = float(reading["temperature"])
    if reading["humidity"]:
        existing_record.humidity = float(reading["humidity"])
    if reading["light_intensity"]:
        existing_record.light_intensity = float(reading["light_intensity"])
    if reading["soil_moisture"]:
        existing_record.soil_moisture = float(reading["soil_moisture"])
    db.session.commit()
    return response

# DELETE or remove an existing reading from the database.
@api.route('/api/readings', methods=['DELETE'])
def delete_reading():
    response = {"errors": None}
    reading_id = request.args.get("reading_id")
    reading = Reading.query.filter_by(id=float(reading_id)).one()
    db.session.delete(reading)
    db.session.commit()
    return response