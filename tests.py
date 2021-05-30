from flask import Flask, request, session, url_for
from models.User import User
from models.Plant import Plant
from models.PlantType import PlantType
from controllers.UserController import LoginForm, RegistrationForm
from controllers.PlantController import PlantRegistrationForm, PlantTypeRegistrationForm
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
    testPlantType = PlantType(plantName, requiredWater, waterFrequency, minTemp, maxTemp, minHumidity, maxHumidity, minMoisture, maxMoisture, idealMoistureLevel, minLightIntensity, maxLightIntensity)
   

    device = Device(testMACAddress, testTime)
    
    
    client = app.test_client()
    
    db.session.add(device)
    db.session.add(testPlantType)
    db.session.commit()
    

    yield ""
    db.session.delete(testPlantType)
    db.session.delete(device)

    # num_rows_deleted = db.session.query(Plant).delete()

    db.session.commit()


@pytest.fixture()
def plant_full_setup(app):
    testPlantType = PlantType(plantName, requiredWater, waterFrequency, minTemp, maxTemp, minHumidity, maxHumidity, minMoisture, maxMoisture, idealMoistureLevel, minLightIntensity, maxLightIntensity)
   

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


def test_plant_form_valid(app):
    form = PlantRegistrationForm(plant_type=testType, level=testLevel, location=testLocation)
    assert not form.validate()

def test_plant_type_register_form_valid(app):
    form = PlantTypeRegistrationForm(name = plantName, requires_water = requiredWater , watering_frequency = waterFrequency , min_temp = minTemp ,
                  max_temp = maxTemp , min_humidity = minHumidity , max_humidity = maxHumidity , min_moisture = minMoisture , max_moisture = maxMoisture ,
                  ideal_moisture_level = idealMoistureLevel , min_light_intensity = minLightIntensity , max_light_intensity = maxLightIntensity )
    assert form.validate()


# Test.No 14
def test_plant_added(app, plant_setup): 
    client = app.test_client()
    plants = Plant.query.all()


    url = "/register/plant/" + testMACAddress
    # print (url)

    receipt = client.post(url, data={'plant_type':testType, 'level':testLevel, 'location':testLocation})
    print (str(receipt.get_data()))
    # client.get('/plants')
    # print (str(receipt.get_data()))
    plants_after = Plant.query.all()
    print (plants_after)

    # plant_types = PlantType.query.all()
    # print (plant_types)



    # assert Plant.query.filter_by(level=testLevel) is not None
    assert len(plants) != len(plants_after)
    

    # db.session.delete(User.query.filter_by(username=testUsername2).one())
    # db.session.commit()
    # Assert for no error message
    # assert not "Error" in str(receipt.get_data())


    


# Test.No 15
def test_plant_not_created(app, plant_full_setup):  
    client = app.test_client()


    client.post("/register/plant", data={'plant_type':testType, 'level':testLevel, 'location':testLocation})

    
    # Check there aren't two entries with the same name
    assert Plant.query.filter_by(level=testLevel).one()

    # Assert for error message 
    # assert "Error" in str(receipt.get_data())





# Test.No 16
def test_plant_not_created_with_missing_element(app, plant_setup): 
    client = app.test_client()
    plants = Plant.query.all()
    client.post("/register/plant", data={'level':testLevel, 'location':testLocation})
    
    plants_after = Plant.query.all()
    assert len(plants) == len(plants_after)
    # plant = Plant.query.filter_by(level=testLevel).one()
    # assert plant is None

    # Assert error,
    # assert "Error" in str(receipt.get_data())

# Test.No 30
def test_add_plant_type(app): 
    client = app.test_client()

    plants_types = PlantType.query.all()
    client.post("/add_plant_type", data={'name':plantName, 'requires_water':requiredWater , 'watering_frequency':waterFrequency , 'min_temp':minTemp ,
                 'max_temp':maxTemp , 'min_humidity':minHumidity , 'max_humidity':maxHumidity , 'min_moisture':minMoisture , 'max_moisture':maxMoisture ,
                 'ideal_moisture_level':idealMoistureLevel , 'min_light_intensity':minLightIntensity , 'max_light_intensity':maxLightIntensity })

    plants_types_after = PlantType.query.all()


    assert not len(plants_types) == len(plants_types_after)


# Test.No 31
def test_cannot_add_duplicate_plant_type(app, plant_setup): 
    client = app.test_client()

    plants_types = PlantType.query.all()
    receipt = client.post("/add_plant_type", data={'name':plantName, 'requires_water':requiredWater , 'watering_frequency':waterFrequency , 'min_temp':minTemp ,
                    'max_temp':maxTemp , 'min_humidity':minHumidity , 'max_humidity':maxHumidity , 'min_moisture':minMoisture , 'max_moisture':maxMoisture ,
                    'ideal_moisture_level':idealMoistureLevel , 'min_light_intensity':minLightIntensity , 'max_light_intensity':maxLightIntensity })
    print (str(receipt.get_data()))
    plants_types_after = PlantType.query.all()


    assert len(plants_types) == len(plants_types_after)

    # Assert Error occurs in reciept




# Test.No 25
def test_delete_plant_type(app, plant_full_setup):
    client = app.test_client()

    plants = Plant.query.all()

    
    client.post("/plant_remove/1", data={'plant_id':1})
    plants_after = Plant.query.all()
    
    assert not len(plants) == len(plants_after)




    

# import flask_unittest
#
# class RegisterUserTest(UserTest):
#     def test_registration(self, client):
#         form = RegistrationForm(request.form)
#         client.post(url_for('register'), data={form: form})
#         self.assertIsNotNone(User.query.first())