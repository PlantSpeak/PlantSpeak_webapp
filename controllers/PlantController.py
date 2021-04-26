from flask import Blueprint, current_app, url_for, request, redirect, render_template, session
from models.Plant import *
from models.PlantType import *
from models.Favourite import *
from models.Reading import *
from database import db
from wtforms import Form, BooleanField, StringField, PasswordField, SelectField, validators
from wtforms.fields.html5 import IntegerField, DecimalField
from flask_table import Table, Col, ButtonCol, LinkCol

plant_pages = Blueprint('plants', __name__, template_folder="views")

class BaseTable(Table):
    classes = ['table', 'table-striped']

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
    view = LinkCol('View', 'plants.show_plant', url_kwargs = dict(plant_id='plant_id'))
    remove_from_saved_list = ButtonCol('Remove', 'plants.saved_list_remove', url_kwargs=dict(plant_id='plant_id'), button_attrs={'class': 'btn btn-danger'})

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

@plant_pages.route('/register/plant', methods=['GET','POST'])
def register():
    form = PlantRegistrationForm(request.form)
    form.plant_type.choices = [(i.id, i.name) for i in PlantType.query.all()]
    if request.method=="POST" and form.validate():
        newPlant = Plant(type=form.plant_type.data, level=form.level.data, location=form.location.data)
        db.session.add(newPlant)
        db.session.commit()
        #session['username'] = newUser.username
        return redirect(url_for('main.home'))
    return render_template("register_plant.html", form=form)

@plant_pages.route('/plant/<plant_id>')
def show_plant(plant_id):
    plant = Plant.query.filter_by(id=plant_id).one()
    latest_reading = Reading.query.filter_by(plant_id=plant.id).order_by(Reading.time.desc()).first()
    return render_template('plant.html', user=user, plant=plant, latest_reading=latest_reading)

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
        plant_records = []
        plants_with_problems=0
        for i in favourites:
            plant = Plant.query.filter_by(id=i.plant_id).one()
            if plant.type:
                plant_type = getPlantType(plant.type)
            else:
                plant_type = "None"
            last_reading = Reading.query.filter_by(plant_id=plant.id).order_by(Reading.time.desc()).first()
            if plant.get_problems(last_reading):
                condition="Needs Attention"
                plants_with_problems+=1
            else:
                condition="Healthy"
            last_seen = str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(last_reading.time)))
            print(last_reading.temperature)
            favourites_records.append(dict(plant_id=i.plant_id, type=plant_type, location=plant.location,
                                      floor=plant.level, condition=condition, alerts=None, last_seen=last_seen))
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