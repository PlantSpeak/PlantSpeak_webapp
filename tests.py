from flask import Flask, request, session, url_for
from models.User import User
from models.Plant import Plant
from models.PlantType import PlantType
from controllers.UserController import LoginForm, RegistrationForm
from database import db

from models.Device import *

import pytest

testUsername = 'test123'
testUsername2 = 'test1234'
testPassword = 'password'
incorrectPassword = 'password!'

testMACAddress = 'A5:A6:BE:C2:16:EA'
testTime = time.time()

testEmail = 'email@example.com'

testType = 'Fern'
testLevel = 2
testLocation = 'Hallway'

plantName = 'Fern'
requiredWater = 50  # requires_water = db.Column(db.Integer)
waterFrequency = 345600    # 4 Days: watering_frequency = db.Column(db.Integer) #Interval in seconds. 
minTemp = 10.0 # min_temp = db.Column(db.Float)
maxTemp = 40.0 # max_temp = db.Column(db.Float)
minHumidity = 25.0 # min_humidity = db.Column(db.Float)
maxHumidity = 70.0 # max_humidity = db.Column(db.Float)
minMoisture = 30.0 # min_moisture = db.Column(db.Float)
maxMoisture = 80.0 # max_moisture = db.Column(db.Float)
idealMoistureLevel = 40 # ideal_moisture_level = db.Column(db.Integer)
minLightIntensity = 20.0 # min_light_intensity = db.Column(db.Float)
maxLightIntensity = 100.0 # max_light_intensity = db.Column(db.Float)
lastWatered = 0 # last_watered = db.Column(db.Integer) # Time in seconds since UNIX epoch.

@pytest.fixture()
def setup(app):
    testUser = User(password=testPassword, username=testUsername, email='email@example.com')
    client = app.test_client()
    db.session.add(testUser)
    db.session.commit()
    yield ""
    db.session.delete(testUser)
    db.session.commit()

def test_register_form_valid(app):
    form = RegistrationForm(username=testUsername, password=testPassword, email=testEmail)
    assert not form.validate()

def test_register_form_invalid_email(app):
    form = RegistrationForm(username=testUsername, password=testPassword, email="test@testcom")
    assert not form.validate()

def test_register_form_invalid_password(app):
    form = RegistrationForm(username=testUsername, password=testPassword, email=testEmail)
    assert not form.validate()

def test_register(app):
    client = app.test_client()
    receipt=client.post("/register", data={'username': testUsername2, 'password': testPassword, 'confirm_password': testPassword, 'email': testEmail})
    with client:
        user = User.query.filter_by(username=testUsername2).one_or_none()
        assert user
        assert user.login(testPassword)
    db.session.delete(User.query.filter_by(username=testUsername2).one())
    db.session.commit()

def test_login(app, setup):
    client = app.test_client()
    client.post("/login", data={'username':testUsername, 'password':testPassword})
    with client:
        client.get('/')
        assert session.get('username') is not None
    assert User.query.filter_by(username=testUsername).one() is not None

def test_incorrect_password(app, setup):
    client = app.test_client()
    receipt = client.post("/login", data={'username':testUsername, 'password':incorrectPassword})
    with client:
        assert "Incorrect password" in str(receipt.get_data())
        assert session.get('username') is None

def test_multiple_incorrect_passwords(app, setup):
    client = app.test_client()
    for i in range(6):
        receipt = client.post("/login", data={'username':testUsername, 'password':incorrectPassword})
    with client:
        assert "You have exceeded the maximum number of password attempts. Please try again later." in str(receipt.get_data())
        assert session.get('username') is None


@pytest.fixture()
def plant_setup(app):
    testPlantType = PlantType(plantName, requiredWater, waterFrequency, minTemp, maxTemp, minHumidity, maxHumidity, minMoisture, maxMoisture, idealMoistureLevel, minLightIntensity, maxLightIntensity, lastWatered)
   

    device = Device(testMACAddress, testTime)
    
    
    client = app.test_client()
    
    db.session.add(device)
    db.session.add(testPlantType)
    db.session.commit()

    testPlant = Plant(type=testPlantType.id, level=testLevel, location=testLocation)
    print(testPlantType.id)
    db.session.add(testPlant)
    db.session.commit()
    

    yield ""
    db.session.delete(testPlant)
    db.session.delete(testPlantType)
    db.session.delete(device)

    # num_rows_deleted = db.session.query(Plant).delete()

    db.session.commit()


# Test.No 14
def test_plant_added(app): 
    client = app.test_client()
    plants = Plant.query.all()
    url = "/register/plant/" + testMACAddress

    receipt = client.post(url, data={'type':testType, 'level':testLevel, 'location':testLocation})
    print (str(receipt.get_data()))
    plants_after = Plant.query.all()
    print (plants_after)




    # assert Plant.query.filter_by(level=testLevel) is not None
    assert len(plants) != len(plants_after)
    

    # db.session.delete(User.query.filter_by(username=testUsername2).one())
    # db.session.commit()
    # 'Check for no "Error" message' 
    # assert not "Error" in str(receipt.get_data())


# Test.No 15
def test_plant_not_created(app, plant_setup):  
    client = app.test_client()

    # device = Device(testMACAddress, time.time())
    # db.session.add(device)
    # db.session.commit()

    # client.post("/register/plant", data={'type':testType, 'level':testLevel, 'location':testLocation})
    # db.session.delete(device)
    # db.session.commit()
    
    # Check there aren't two entries with the same name
    assert Plant.query.filter_by(level=testLevel).one()


    # db.session.delete(device)
    # db.session.commit()

    # Check for an error message 
    # assert "Error" in str(receipt.get_data())

# Test.No 16
def test_plant_not_created_without_plant_type(app, plant_setup): 
    client = app.test_client()
    plants = Plant.query.all()
    client.post("/register/plant", data={'level':testLevel, 'location':testLocation})
    plants_after = Plant.query.all()
    assert len(plants) == len(plants_after)
    # plant = Plant.query.filter_by(level=testLevel).one()
    # assert plant is None

# Error pertaining to missing plant_type  
    # assert "Error" in str(receipt.get_data())

# Test.No 30
# def test_add_plant_type(user): 
#     client = app.test_client()


# import flask_unittest
#
# class RegisterUserTest(UserTest):
#     def test_registration(self, client):
#         form = RegistrationForm(request.form)
#         client.post(url_for('register'), data={form: form})
#         self.assertIsNotNone(User.query.first())