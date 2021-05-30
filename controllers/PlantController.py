from flask import Blueprint, current_app, url_for, request, redirect, render_template, session, flash
from models.Plant import *
from models.PlantType import *
from models.Favourite import *
from models.Reading import *
from models.Device import *
from database import db
from wtforms import Form, BooleanField, StringField, PasswordField, SelectField, validators
from wtforms.fields.html5 import IntegerField, DecimalField
from flask_table import Table, Col, ButtonCol, LinkCol
import time
import pygal
from pygal.style import Style
from datetime import datetime, timedelta
import calendar

# Registers this blueprint with the main app context.
plant_pages = Blueprint('plants', __name__, template_folder="views")

# Runs for every page where user authentication is required.
def check_logged_in():
    if not session.get('user_id'):
        flash("Please log in to continue.", category="warning")
        return False
    return True

# TABLES
#  Defining tables to be processed for endpoint functions and on-page rendering by Flask-Table.
class BaseTable(Table):
    classes = ['table', 'table-striped']

class DeviceTable(BaseTable):
    id = Col('Device ID')
    favourite = ButtonCol('Add Plant', 'plants.register', url_kwargs=dict(device_id='id'),
                          button_attrs={'class': 'btn btn-success'})
    mac_address = Col('MAC Address')
    last_seen = Col('Last Seen')
    label = Col('label')
    location = Col('location')

class PlantTable(BaseTable):
    plant_id = Col('Plant ID')
    type = Col('Plant Type')
    location = Col('Location')
    level = Col('Floor')
    favourite = ButtonCol('Favourite', 'plants.add_favourite', url_kwargs=dict(plant_id='plant_id'), button_attrs={'class': 'btn btn-success'})
    remove_from_saved_list = ButtonCol('Remove', 'plants.plant_remove', url_kwargs=dict(plant_id='plant_id'), button_attrs={'class': 'btn btn-danger'})

def create_fa_symbol(tooltip_message, symbol, colour):
    return """<span class="d-inline-block" data-bs-toggle="tooltip"  title="%s" data-bs-animation=true style="color:%s">
          <i class="fa %s"></i>
    </span>""" % (tooltip_message, symbol, colour)

# Custom column type override for Flask-Table
class ProblemsCol(Col):
    def td_format(self, content):
        problem_list = []
        if content:
            if content.values():
                if content['temperature_high']:
                    problem_list.append(create_fa_symbol("Temperature too high.", "red", "fa-thermometer-full"))
                if content['temperature_low']:
                    problem_list.append(create_fa_symbol("Temperature too low.", "skyblue", "fa-snowflake"))
                if content['humidity_low']:
                    problem_list.append(create_fa_symbol("Humidity too low.", "skyblue", "fa-water"))
                if content['humidity_high']:
                    problem_list.append(create_fa_symbol("Humidity too high..", "skyblue", "fa-water"))
                if content['moisture_low']:
                    problem_list.append(create_fa_symbol("Soil moisture too low.", "blue", "fa-tint-slash"))
                if content['moisture_high']:
                    problem_list.append(create_fa_symbol("Soil moisture too high.", "blue", "fa-tint"))
                if content['light_intensity_low']:
                    problem_list.append(create_fa_symbol("Light Intensity too low.", "orange", "far fa-lightbulb"))
                if content['light_intensity_high']:
                    problem_list.append(create_fa_symbol("Light Intensity too high.", "orange", "fas fa-lightbulb"))
                return problem_list
        return ""

class SavedListTable(BaseTable):
    plant_id = Col('Plant ID')
    type = Col('Plant Type')
    location = Col('Location')
    floor = Col('Floor')
    condition = Col('Condition')
    alerts = ProblemsCol('Alerts')
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
    plant_type = SelectField('Plant Type')
    level = IntegerField('Plant Level')
    location = StringField('Plant Location', validators=[validators.Length(min=LOCATION_MIN_LENGTH, max=LOCATION_MAX_LENGTH)])

# Get plants from the user's saved list, based on a list of their ids.
def getSavedList(plant_ids):
    saved_list = []
    for i in plant_ids:
        Plant.query.filter_by(id=i)
    return saved_list

def getPlantType(plant_id):
    plant_type = PlantType.query.filter_by(id=plant_id).one()
    return plant_type.name

# Remove plant from system (and DB).
@plant_pages.route('/plant_remove/<plant_id>', methods=['GET','POST'])
def plant_remove(plant_id):
    if not check_logged_in():
        return redirect(url_for('users.login'))
    favourites = Favourite.query.filter_by(plant_id=plant_id).all()
    for i in favourites:
        db.session.delete(i)
    db.session.commit()
    plant = Plant.query.filter_by(id=plant_id).one()
    db.session.delete(plant)
    db.session.commit()
    return redirect(request.referrer)

# Add favourite plant for user (i.e. add to saved list of plants).
@plant_pages.route('/add_favourite/<plant_id>', methods=['GET','POST'])
def add_favourite(plant_id):
    if Favourite.query.filter_by(plant_id=plant_id).one_or_none():
        flash("You have already added that plant to your favourites list.", category="warning")
        return redirect(request.referrer)
    if not check_logged_in():
        return redirect(url_for('users.login'))
    if session.get('user_id') is not None:
        favourite = Favourite(session['user_id'], plant_id)
        db.session.add(favourite)
        db.session.commit()
        flash("Plant added to favourites list!", category="success")
        return redirect(request.referrer)
    else:
        return redirect(url_for('users.login'))

# Show all plants added to the system (devices which have been paired and assigned a plant type/location details).
@plant_pages.route('/plants')
def show_plants():
    if not check_logged_in():
        return redirect(url_for('users.login'))
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
    if not check_logged_in():
        return redirect(url_for('users.login'))
    device = Device.query.filter_by(id=device_id).first()
    form = PlantRegistrationForm(request.form)
    form.plant_type.choices = [(i.id, i.name) for i in PlantType.query.all()]
    if not device:
        flash("No device exists for this plant. Please use a device listed below.", category="danger")
        return redirect(url_for('plants.show_devices'))
    else:
        if request.method=="POST" and form.validate():
            newPlant = Plant(type=form.plant_type.data, level=form.level.data, location=form.location.data, mac_address=device.mac_address)
            if not Plant.query.filter_by(type=newPlant.type, level=newPlant.level, location=newPlant.location).all() and not Plant.query.filter_by(mac_address=newPlant.mac_address).all():
                device = Device.query.filter_by(id=device_id).one()
                device.registered = 1
                db.session.add(newPlant)
                db.session.commit()
                return redirect(url_for('main.home'))
            else:
                flash("A plant with those details already exists!", category="danger")
    return render_template("register_plant.html", form=form)

# Pygal chart preparation helper functions for the plant details/report page.
def prepare_readings_chart(attribute, attribute_name, readings, x_label_count, y_min, y_max, x_label, y_label, line_colour, logarithmic):
    style = Style(font_family="Arial",  colors=[line_colour], background='transparent')
    temp_chart = pygal.DateTimeLine(x_label_rotation=20, range=(y_min, y_max),
                               show_minor_x_labels=False, show_major_x_labels=True,
                               x_labels_major_count=x_label_count, show_legend=False, style=style,
                                    x_title=x_label, y_title=y_label, logarithmic=logarithmic,
                                    x_value_formatter=lambda dt: dt.strftime('%H:%M %p'))
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

def prepare_daily_average_chart(records, attribute_name,  x_label_count, y_min, y_max, x_label, y_label, line_colour, logarithmic):
    style = Style(font_family="Arial", colors=[line_colour], background='transparent')
    temp_chart = pygal.Line(x_label_rotation=20, range=(y_min, y_max),
                                    show_minor_x_labels=False, show_major_x_labels=True,
                                    x_labels_major_count=x_label_count, show_legend=False, style=style,
                                    x_title=x_label, y_title=y_label, logarithmic=logarithmic)
    temp_chart.add(attribute_name, [i[1] for i in records])
    temp_chart.x_labels = reversed([i[0] for i in records])
    chart = temp_chart.render_data_uri()
    return chart

# Prepares page for displaying individual plant's details and previous readings report.
@plant_pages.route('/plant/<plant_id>')
def show_plant(plant_id):
    # Database queries to get info to display on page.
    plant = Plant.query.filter_by(id=plant_id).one_or_none()
    plant_type = PlantType.query.filter_by(id=plant.type).one().name
    latest_reading = Reading.query.filter_by(mac_address=plant.mac_address).order_by(Reading.time.desc()).first()

    readings = Reading.query.filter_by(mac_address=plant.mac_address).order_by(Reading.time.desc()).limit(100)
    temperature_chart = prepare_readings_chart('temperature', 'Temperature', readings, 10, 0, 50, "Time", "Temperature (°C)", "#FF0000", False)
    humidity_chart = prepare_readings_chart('humidity', 'Humidity', readings, 10, 0, 100, "Time", "Humidity (%)", "#0055FF", False)
    soil_moisture_chart = prepare_readings_chart('soil_moisture', 'Soil Moisture', readings, 10, 0, 100, "Time", "Volumetric Soil Moisture (%)", "#0000FF", False)
    light_intensity_chart = prepare_readings_chart('light_intensity', 'Light Intensity', readings, 10, 0, 1000, "Time", "Light Intesity (lux)", "#FFAA00", True)

    # String formatters for displaying data/times on charts.
    percent_formatter = lambda x: '{:.10g}%'.format(x)
    temperature_formatter = lambda x: u'{:.10g}°C'.format(x)
    lux_formatter = lambda x: u'{:.10g} lux'.format(x)

    # Visually-appealing gauge charts displayed at top of page for latest reading.
    temp_gauge = prepare_gauge_indicator('temperature',"Temperature",latest_reading,0,50,temperature_formatter,"#FF0000", False)
    humidity_gauge = prepare_gauge_indicator('humidity',"Humidity",latest_reading,0,100,percent_formatter,"#0055FF", False)
    soil_moisture_gauge = prepare_gauge_indicator('soil_moisture',"Soil Moisture",latest_reading,0,100,percent_formatter,"#0000FF", False)
    light_intensity_gauge = prepare_gauge_indicator('light_intensity',"Light Intensity",latest_reading,0,1000,lux_formatter,"#FFAA00", True)

    # Prepare the table of all recent readings.
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

    # Preparing charts of average daily readings over month.
    MONTH_LENGTH=2592000
    readings_month = Reading.query.filter_by(mac_address=plant.mac_address).filter(time.time()-Reading.time<=MONTH_LENGTH).order_by(Reading.time.desc()).all()

    days = {}
    for i in readings_month:
        dt = datetime.fromtimestamp(i.time).date()
        if not dt in days.keys():
            days[dt] = []
        days[dt].append(i)

    month_avgs = {}

    for i in days.keys():
        month_avgs[i] = {}
        temps = [j.temperature for j in days[i]]
        humidities = [j.humidity for j in days[i]]
        soil_moistures = [j.soil_moisture for j in days[i]]
        light_intensities = [j.light_intensity for j in days[i]]
        month_avgs[i]["temperature"] = sum(temps)/len(temps)
        month_avgs[i]["humidity"] = sum(humidities)/len(humidities)
        month_avgs[i]["soil_moisture"] = sum(soil_moistures)/len(soil_moistures)
        month_avgs[i]["light_intensity"] = sum(light_intensities)/len(light_intensities)

    # Preparing charts of average daily readings over week.
    week_records = []
    min_date = datetime.now().date()-timedelta(days=7)
    for i in month_avgs.keys():
        if i<=datetime.now().date() and i>=min_date:
            week_records.append((str(i), month_avgs[i]))

    week_temperatures = [(i[0], i[1]["temperature"]) for i in week_records]
    week_humidities = [(i[0], i[1]["humidity"]) for i in week_records]
    week_soil_moisture = [(i[0], i[1]["soil_moisture"]) for i in week_records]
    week_light_intensities = [(i[0], i[1]["light_intensity"]) for i in week_records]

    week_temperature_chart = prepare_daily_average_chart(week_temperatures, "Temperature", 7, 0, 50, "Date", "Temperature", "red", False)
    week_humidity_chart = prepare_daily_average_chart(week_humidities, "Humidity", 7, 0, 100, "Date", "Humidity", "#0055FF", False)
    week_soil_moisture_chart = prepare_daily_average_chart(week_soil_moisture, "Soil Moisture", 7, 0, 100, "Date", "Soil Moisture (%)", "#0000FF", False)
    week_light_intensity_chart = prepare_daily_average_chart(week_light_intensities, "Light Intensity", 7, 0, 1000, "Date", "Light Intensity (lux)", "#FFAA00", True)

    month_records = []
    for i in month_avgs.keys():
        month_records.append((str(i), month_avgs[i]))

    month_temperatures = [(i[0], i[1]["temperature"]) for i in month_records]
    month_humidities = [(i[0], i[1]["humidity"]) for i in month_records]
    month_soil_moisture = [(i[0], i[1]["soil_moisture"]) for i in month_records]
    month_light_intensities = [(i[0], i[1]["light_intensity"]) for i in month_records]

    month_temperature_chart = prepare_daily_average_chart(month_temperatures, "Temperature", 7, 0, 50, "Date",
                                                         "Temperature", "red", False)
    month_humidity_chart = prepare_daily_average_chart(month_humidities, "Humidity", 7, 0, 100, "Date", "Humidity", "#0055FF",
                                                      False)
    month_soil_moisture_chart = prepare_daily_average_chart(month_soil_moisture, "Soil Moisture", 7, 0, 100, "Date",
                                                           "Soil Moisture (%)", "#0000FF", False)
    month_light_intensity_chart = prepare_daily_average_chart(month_light_intensities, "Light Intensity", 7, 0, 1000,
                                                             "Date", "Light Intensity (lux)", "#FFAA00", True)
    latest_reading_time = time.strftime("%r on %Y-%m-%d", time.localtime(latest_reading.time))

    return render_template('plant.html', plant=plant, latest_reading=latest_reading,
                           temperature_chart=temperature_chart, humidity_chart=humidity_chart,
                           soil_moisture_chart=soil_moisture_chart, light_intensity_chart=light_intensity_chart,
                           temp_gauge=temp_gauge, humidity_gauge=humidity_gauge,
                           soil_moisture_gauge=soil_moisture_gauge,
                           light_intensity_gauge=light_intensity_gauge,
                           table=table,
                           plant_type=plant_type,
                           week_temperature_chart=week_temperature_chart,
                           week_humidity_chart=week_humidity_chart,
                           week_soil_moisture_chart=week_soil_moisture_chart,
                           week_light_intensity_chart=week_light_intensity_chart,
                           month_temperature_chart=month_temperature_chart,
                           month_humidity_chart=month_humidity_chart,
                           month_soil_moisture_chart=month_soil_moisture_chart,
                           latest_reading_time=latest_reading_time,
                           month_light_intensity_chart=month_light_intensity_chart)

@plant_pages.route('/saved_plant_remove/<plant_id>', methods=['GET','POST'])
def saved_list_remove(plant_id):
    if not check_logged_in():
        return redirect(url_for('users.login'))
    plant = Favourite.query.filter_by(plant_id=plant_id).one()
    db.session.delete(plant)
    db.session.commit()
    return redirect(request.referrer)


@plant_pages.route('/dashboard')
def dashboard():
    if session.get('user_id') is not None:
        favourites = Favourite.query.filter_by(user_id=session.get('user_id')).all()
        favourites_records = []
        problems_records = []
        plants_with_problems=0
        # Iterate over all plants to get their latest reading(s) and prepare a summary of their current state.
        for i in favourites:
            plant = Plant.query.filter_by(id=i.plant_id).one()
            if plant.type:
                plant_type = getPlantType(plant.type)
            else:
                plant_type = "None"
            last_reading = Reading.query.filter_by(mac_address=plant.mac_address).order_by(Reading.time.desc()).first()
            if not last_reading:
                continue
            problems = plant.get_problems(last_reading)
            problem_list = []
            last_seen = str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(last_reading.time)))
            if True in problems.values():
                condition = "Needs Attention"
                plants_with_problems += 1
                problems_records.append(dict(plant_id=i.plant_id, type=plant_type, location=plant.location,
                                             floor=plant.level, condition=condition, alerts=problems,
                                             last_seen=last_seen))

            else:
                condition = "Healthy"
                favourites_records.append(dict(plant_id=i.plant_id, type=plant_type, location=plant.location,
                                               floor=plant.level, condition=condition, alerts=problems,
                                               last_seen=last_seen))

            if not problem_list:
                problem_list = "None"

        # Prepare the tables of saved items/favourite plants to be displayed on the dashboard.
        problems_table = SavedListTable(problems_records, classes=["table table-striped"])
        table = SavedListTable(favourites_records, classes=["table table-striped"])
        return render_template('dashboard.html', problems_table=problems_table, table=table, plants_with_problems=plants_with_problems)
    else:
        return redirect(url_for('users.login'))

class PlantTypeRegistrationForm(Form):
    plant_type = StringField(validators=[validators.required()])
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
                                                 validators.NumberRange(min=0,max=100)])
    ideal_soil_moisture_level = SelectField(choices=[(0, 'Dry'), (1, 'Moist'), (2, 'Wet')],
                                            validators=[validators.optional()])
    min_light_intensity = IntegerField(validators=[validators.optional(),
                                                   validators.NumberRange(min=0)])
    max_light_intensity = IntegerField(validators=[validators.optional(),
                                                   validators.NumberRange(min=0)])

@plant_pages.route('/add_plant_type', methods=['GET','POST'])
def add_plant_type():
    if not check_logged_in():
        return redirect(url_for('users.login'))
    form = PlantTypeRegistrationForm(request.form)
    # Load in choices at runtime (with app context).
    if request.method=="POST":
        if form.validate():
            if form.requires_water.data:
                requires_water = 1
                try:
                    watering_interval = int(form.watering_frequency_unit.data) / form.watering_frequency_interval.data
                except:
                    flash("Invalid watering interval.", category="danger")
                    return render_template("add_plant_type.html", form=form)
            else:
                requires_water = 0
                watering_interval = 0

            existing = PlantType.query.filter_by(name=form.plant_type.data).one_or_none()

            if not existing:
                newPlantType = PlantType(form.plant_type.data, requires_water, watering_interval,
                                         form.min_temp.data, form.max_temp.data, form.min_humidity.data, form.max_humidity.data,
                                         form.min_soil_moisture.data, form.max_soil_moisture.data, form.ideal_soil_moisture_level.data,
                                         form.min_light_intensity.data, form.max_light_intensity.data)
                db.session.add(newPlantType)
                db.session.commit()
                return redirect(url_for('plants.show_devices'))
            else:
                flash("A plant with that name already exists.", category="danger")
                return render_template("add_plant_type.html", form=form)
        else:
            flash("There were issues with your inputs.", category="danger")
    return render_template("add_plant_type.html", form=form)

@plant_pages.route('/devices', methods=['GET','POST'])
def show_devices():
    if not check_logged_in():
        return redirect(url_for('users.login'))
    DEVICE_TIMEOUT = 300 # 5 Minute timeout
    devices = Device.query.filter(Device.last_seen >= time.time()-DEVICE_TIMEOUT).all()
    devices_table_items = []
    for i in devices:
        if Plant.query.filter_by(mac_address=i.mac_address).count()==0:
            last_seen = str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(i.last_seen)))
            devices_table_items.append(dict(id=i.id, mac_address=i.mac_address, last_seen=last_seen,
                                            label=i.label, location=i.location))
    table = DeviceTable(devices_table_items, classes=["table table-sm table-striped"])
    return render_template("device.html", table=table)