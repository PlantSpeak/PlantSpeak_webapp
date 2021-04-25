from flask import Blueprint, current_app, url_for, request, redirect, render_template, session
from models.Plant import *
from models.PlantType import *
from database import db
from wtforms import Form, BooleanField, StringField, PasswordField, SelectField, validators
from wtforms.fields.html5 import IntegerField, DecimalField
from flask_table import Table, Col

plant_pages = Blueprint('plants', __name__, template_folder="views")

class PlantTable(Table):
    type = Col('Plant Type')
    location = Col('Location')
    floor = Col('Floor')
    date_added = Col('Date Added')

class DashboardTable(Table):
    type = Col('Plant Type')
    location = Col('Location')
    floor = Col('Floor')
    condition = Col('Condition')
    alerts = Col('Alerts')
    icon = Col('Icon')
    last_seen = Col('Last Seen')

class PlantRegistrationForm(Form):
    #plantname = StringField('Plant Name', [validators.Length(min=NAME_MIN_LENGTH, max=NAME_MAX_LENGTH)])
    plant_type = SelectField('Plant Type')
    level = StringField('Plant Level', [validators.Length(min=LEVEL_MIN_LENGTH, max=LEVEL_MAX_LENGTH)])
    location = StringField('Plant Location', [validators.Length(min=LOCATION_MIN_LENGTH, max=LOCATION_MAX_LENGTH)])

@plant_pages.route('/plants')
def show_plants():
    plants = Plant.query.all()
    return render_template("plants.html", plants=plants)

@plant_pages.route('/register/plant', methods=['GET','POST'])
def register():
    form = PlantRegistrationForm(request.form)
    form.plant_type.choices = [(i.id, i.name) for i in PlantType.query.all()]
    if request.method=="POST" and form.validate():
        newPlant = Plant(level=form.level.data, location=form.location.data)
        db.session.add(newPlant)
        db.session.commit()
        #session['username'] = newUser.username
        return redirect(url_for('main.home'))
    return render_template("register_plant.html", form=form)

@plant_pages.route('/plant/<plant_id>')
def show_plant(plant_id):
    plant = Plant.query.filter_by(id=plant_id)
    return render_template('plant.html', plant=plant)

@plant_pages.route('/dashboard')
def dashboard():
    user_id = session['user_id']
    user = User.query.filter_by(id=user_id)
    table = DashboardTable()
    return render_template('dashboard.html', table=table)

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
    return render_template("add_plant_type.html", form=form)