from flask import Blueprint, current_app, url_for, request, redirect, render_template, session
from models.Plant import *
from models.PlantType import *
from models.Favourite import *
from models.Reading import *
from models.Device import *
from database import db
from wtforms import Form, BooleanField, StringField, PasswordField, SelectField, validators
from wtforms.fields.html5 import IntegerField, DecimalField
from flask_table import Table, Col, ButtonCol, LinkCol

plant_pages = Blueprint('plants', __name__, template_folder="views")

class BaseTable(Table):
    classes = ['table', 'table-striped']

class DeviceTable(BaseTable):
    id = Col('Device ID')
    mac_address = Col('MAC Address')
    last_seen = Col('Last Seen')
    label = Col('label')
    location = Col('location')
    favourite = ButtonCol('Add Plant', 'plants.register', url_kwargs=dict(device_id='id'), button_attrs={'class': 'btn btn-success'})

class PlantTable(BaseTable):
    plant_id = Col('Plant ID')
    type = Col('Plant Type')
    location = Col('Location')
    level = Col('Floor')
    favourite = ButtonCol('Favourite', 'plants.add_favourite', url_kwargs=dict(plant_id='plant_id'), button_attrs={'class': 'btn btn-success'})
    remove_from_saved_list = ButtonCol('Remove', 'plants.plant_remove', url_kwargs=dict(plant_id='plant_id'), button_attrs={'class': 'btn btn-danger'})

class SavedListTable(BaseTable):
    plant_id = Col('Plant ID')
    type = Col('Plant Type')
    location = Col('Location')
    floor = Col('Floor')
    condition = Col('Condition')
    alerts = Col('Alerts')
    last_seen = Col('Last Seen')
    view = LinkCol('View', 'plants.show_plant', url_kwargs=dict(plant_id='plant_id'))
    remove_from_saved_list = ButtonCol('Remove', 'plants.saved_list_remove', url_kwargs=dict(plant_id='plant_id'), button_attrs={'class': 'btn btn-danger'})

class ReadingsTable(BaseTable):
    time = Col('Time')
    temperature = Col('Temperature (°C)')
    humidity = Col('Humidity (%)')
    soil_moisture = Col('Soil Moisture (%)')
    light_intensity = Col('Light Intensity (lux)')

class PlantRegistrationForm(Form):
    #plantname = StringField('Plant Name', [validators.Length(min=NAME_MIN_LENGTH, max=NAME_MAX_LENGTH)])
    plant_type = SelectField('Plant Type')
    level = StringField('Plant Level')
    location = StringField('Plant Location', [validators.Length(min=LOCATION_MIN_LENGTH, max=LOCATION_MAX_LENGTH)])

def getSavedList(plant_ids):
    saved_list = []
    for i in plant_ids:
        Plant.query.filter_by(id=i)
    return saved_list

def getPlantType(plant_id):
    print(plant_id)
    plant_type = PlantType.query.filter_by(id=plant_id).one()
    return plant_type.name

@plant_pages.route('/plant_remove/<plant_id>', methods=['GET','POST'])
def plant_remove(plant_id):
    favourites = Favourite.query.filter_by(plant_id=plant_id).all()
    for i in favourites:
        db.session.delete(i)
    db.session.commit()
    plant = Plant.query.filter_by(id=plant_id).one()
    db.session.delete(plant)
    db.session.commit()
    return redirect(request.referrer)
#
# @plant_pages.route('/plant/<id>')
# def show_plant(id):
#     return render_template()

@plant_pages.route('/add_favourite/<plant_id>', methods=['GET','POST'])
def add_favourite(plant_id):
    if session.get('user_id') is not None:
        favourite = Favourite(session['user_id'], plant_id)
        db.session.add(favourite)
        db.session.commit()
        return redirect(request.referrer)
    else:
        return redirect(url_for('users.login'))

@plant_pages.route('/plants')
def show_plants():
    plants = Plant.query.all()
    plant_records = []
    for i in plants:
        if i.type:
            plant_type = getPlantType(i.type)
        else:
            plant_type = "None"
        plant_record = dict(plant_id=i.id, type=plant_type, location=i.location, level=i.level)
        plant_records.append(plant_record)
    table = PlantTable(plant_records)
    return render_template("plants.html", table=table)

@plant_pages.route('/register/plant/<device_id>', methods=['GET','POST'])
def register(device_id):
    device = Device.query.filter_by(id=device_id).first()
    form = PlantRegistrationForm(request.form)
    form.plant_type.choices = [(i.id, i.name) for i in PlantType.query.all()]
    if request.method=="POST" and form.validate():
        newPlant = Plant(type=form.plant_type.data, level=form.level.data, location=form.location.data, mac_address=device.mac_address)
        device = Device.query.filter_by(id=device_id).one()
        device.registered = 1
        db.session.add(newPlant)
        db.session.commit()
        return redirect(url_for('main.home'))
    return render_template("register_plant.html", form=form)

import pygal
from pygal.style import Style
from datetime import datetime, timedelta

def prepare_readings_chart(attribute, attribute_name, readings, x_label_count, y_min, y_max, x_label, y_label, line_colour, logarithmic):
    style = Style(font_family="Arial",  colors=[line_colour], background='transparent')
    temp_chart = pygal.DateTimeLine(x_label_rotation=20, range=(y_min, y_max),
                               show_minor_x_labels=False, show_major_x_labels=True,
                               x_labels_major_count=x_label_count, show_legend=False, style=style,
                                    x_title=x_label, y_title=y_label, logarithmic=logarithmic)
    temp_chart.add(attribute_name, [(datetime.fromtimestamp(i.time), getattr(i, attribute)) for i in readings])
    chart = temp_chart.render_data_uri()
    return chart

def prepare_gauge_indicator(attribute, attribute_name, latest_reading, min_val, max_val, val_formatter, colour, logarithmic):
    style = Style(font_family="Arial",  colors=[colour], value_font_size=36, label_font_size=24, title_font_size=48,
                  background='transparent'
                  )
    gauge = pygal.SolidGauge(
        half_pie=True, inner_radius=0.70,
        style=style, show_legend=False, margin_top=-200, margin_bottom=-100, logarithmic=logarithmic)
    gauge.title=attribute_name
    gauge.add('Temperature', [{'value':  getattr(latest_reading, attribute), 'min_value': min_val, 'max_value': max_val}], formatter=val_formatter)
    return gauge.render(is_unicode=True)

@plant_pages.route('/plant/<plant_id>')
def show_plant(plant_id):
    plant = Plant.query.filter_by(id=plant_id).one()
    plant_type = PlantType.query.filter_by(id=plant.type).one().name
    latest_reading = Reading.query.filter_by(mac_address=plant.mac_address).order_by(Reading.time.desc()).first()

    readings = Reading.query.filter_by(mac_address=plant.mac_address).order_by(Reading.time.desc()).limit(100)
    temperature_chart = prepare_readings_chart('temperature', 'Temperature', readings, 10, 0, 50, "Time", "Temperature (°C)", "#FF0000", False)
    humidity_chart = prepare_readings_chart('humidity', 'Humidity', readings, 10, 0, 100, "Time", "Humidity (%)", "#0000FF", False)
    soil_moisture_chart = prepare_readings_chart('soil_moisture', 'Soil Moisture', readings, 10, 0, 100, "Time", "Volumetric Soil Moisture (%)", "#0000FF", False)
    light_intensity_chart = prepare_readings_chart('light_intensity', 'Light Intensity', readings, 10, 0, 1000, "Time", "Light Intesity (lux)", "#FFAA00", True)

    percent_formatter = lambda x: '{:.10g}%'.format(x)
    temperature_formatter = lambda x: u'{:.10g}°C'.format(x)
    lux_formatter = lambda x: u'{:.10g} lux'.format(x)

    temp_gauge = prepare_gauge_indicator('temperature',"Temperature",latest_reading,0,50,temperature_formatter,"#FF0000", False)
    humidity_gauge = prepare_gauge_indicator('humidity',"Humidity",latest_reading,0,100,percent_formatter,"#0000FF", False)
    soil_moisture_gauge = prepare_gauge_indicator('soil_moisture',"Soil Moisture",latest_reading,0,100,percent_formatter,"#0000FF", False)
    light_intensity_gauge = prepare_gauge_indicator('light_intensity',"Light Intensity",latest_reading,0,1000,lux_formatter,"#FA0000", True)

    # gauge.add('Humidity', [{'value':  latest_reading.humidity, 'min_value': 0, 'max_value': 100}], formatter=percent_formatter)
    # gauge.add('Soil Moisture', [{'value':  latest_reading.soil_moisture, 'min_value': 0, 'max_value': 50}], formatter=percent_formatter)
    # gauge.add('Light Intensity', [{'value': latest_reading.light_intensity, 'min_value': 0, 'max_value':1000}])
    # temp_gauge = gauge.render(is_unicode=True)

    readings_records = []
    for i in readings:
        readings_records.append(dict(
            temperature=i.temperature,
            humidity=i.humidity,
            soil_moisture=i.soil_moisture,
            light_intensity=i.light_intensity,
            time=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(i.time))
        ))
    table = ReadingsTable(readings_records)

    return render_template('plant.html', plant=plant, latest_reading=latest_reading,
                           temperature_chart=temperature_chart, humidity_chart=humidity_chart,
                           soil_moisture_chart=soil_moisture_chart, light_intensity_chart=light_intensity_chart,
                           temp_gauge=temp_gauge, humidity_gauge=humidity_gauge,
                           soil_moisture_gauge=soil_moisture_gauge,
                           light_intensity_gauge=light_intensity_gauge,
                           table=table,
                           plant_type=plant_type)

@plant_pages.route('/saved_plant_remove/<plant_id>', methods=['GET','POST'])
def saved_list_remove(plant_id):
    plant = Favourite.query.filter_by(plant_id=plant_id).one()
    db.session.delete(plant)
    db.session.commit()
    return redirect(request.referrer)

@plant_pages.route('/dashboard')
def dashboard():
    if session.get('user_id') is not None:
        # user = User.query.filter_by(id=user_id)
        favourites = Favourite.query.filter_by(user_id=session.get('user_id')).all()
        favourites_records = []
        plants_with_problems=0
        for i in favourites:
            plant = Plant.query.filter_by(id=i.plant_id).one()
            if plant.type:
                plant_type = getPlantType(plant.type)
            else:
                plant_type = "None"
            last_reading = Reading.query.filter_by(mac_address=plant.mac_address).order_by(Reading.time.desc()).first()
            problems = plant.get_problems(last_reading)
            problem_list = []
            if problems:
                condition = "Needs Attention"
                plants_with_problems += 1
                if problems['temperature_low']:
                    problem_list.append("Low Temperature")
                if problems['temperature_high']:
                    problem_list.append("High Temperature")
                if problems['humidity_low']:
                    problem_list.append("Low Humidity")
                if problems['humidity_high']:
                    problem_list.append("High Humidity")
                if problems['moisture_low']:
                    problem_list.append("Low Soil Moisture")
                if problems['moisture_high']:
                    problem_list.append("High Soil Moisture")
                if problems['light_intensity_low']:
                    problem_list.append("Too little light")
                if problems['light_intensity_high']:
                    problem_list.append("Too light")
            else:
                condition = "Healthy"
            if not problem_list:
                problem_list = "None"


            last_seen = str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(last_reading.time)))
            print(last_reading.temperature)
            favourites_records.append(dict(plant_id=i.plant_id, type=plant_type, location=plant.location,
                                      floor=plant.level, condition=condition, alerts=problem_list, last_seen=last_seen))
        print(favourites_records)
        table = SavedListTable(favourites_records)
        return render_template('dashboard.html', table=table, plants_with_problems=plants_with_problems)
    else:
        return redirect(url_for('users.login'))

class PlantTypeRegistrationForm(Form):
    plant_type = StringField()
    requires_water = BooleanField()
    watering_frequency_interval = IntegerField(label="", validators=[validators.optional()])
    watering_frequency_unit = SelectField(label="",
                                          choices=[(60, 'minute'), (3600, 'hour'),
                                                   (86400, 'day'), (604800, 'week')],
                                          validators=[validators.optional()])
    min_temp = DecimalField(places=1, validators=[validators.optional(),
                                                  validators.NumberRange(min=-273.15,max=100)])
    max_temp = DecimalField(places=1, validators=[validators.optional(),
                                                  validators.NumberRange(min=-273.15,max=100)])
    min_humidity = DecimalField(places=1, validators=[validators.optional(),
                                                      validators.NumberRange(min=0,max=100)])
    max_humidity = DecimalField(places=1, validators=[validators.optional(),
                                                      validators.NumberRange(min=0,max=100)])
    min_soil_moisture = IntegerField(validators=[validators.optional(),
                                                 validators.NumberRange(min=0,max=100)])
    max_soil_moisture = IntegerField(validators=[validators.optional(),
                                                 validators.NumberRange(min=-273.15,max=100)])
    ideal_soil_moisture_level = SelectField(choices=[(0, 'Dry'), (1, 'Moist'), (2, 'Wet')],
                                            validators=[validators.optional()])
    min_light_intensity = IntegerField(validators=[validators.optional(),
                                                   validators.NumberRange(min=0,max=100)])
    max_light_intensity = IntegerField(validators=[validators.optional(),
                                                   validators.NumberRange(min=0,max=100)])

@plant_pages.route('/add_plant_type', methods=['GET','POST'])
def add_plant_type():
    form = PlantTypeRegistrationForm(request.form)
    # Load in choices at runtime (with app context).
    if request.method=="POST" and form.validate():
        print(form.watering_frequency_unit.data, form.watering_frequency_interval.data)
        newPlantType = PlantType(form.plant_type.data, form.requires_water.data, int(form.watering_frequency_unit.data)/form.watering_frequency_interval.data,
                                 form.min_temp.data, form.max_temp.data, form.min_humidity.data, form.max_humidity.data,
                                 form.min_soil_moisture.data, form.max_soil_moisture.data, form.ideal_soil_moisture_level.data,
                                 form.min_light_intensity.data, form.max_light_intensity.data)
        db.session.add(newPlantType)
        db.session.commit()
        return redirect(url_for('main.home'))
    return render_template("add_plant_type.html", form=form)

@plant_pages.route('/devices', methods=['GET','POST'])
def show_devices():
    devices = Device.query.all()
    devices_table_items = []
    for i in devices:
        last_seen = str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(i.last_seen)))
        devices_table_items.append(dict(id=i.id, mac_address=i.mac_address, last_seen=last_seen,
                                        label=i.label, location=i.location))
    table = DeviceTable(devices_table_items)
    return render_template("device.html", table=table)