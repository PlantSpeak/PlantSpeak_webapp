from flask import Blueprint, current_app, url_for, request, redirect, render_template, session

main_pages = Blueprint('main', __name__, template_folder="views")
@main_pages.route('/')
def home():
    return render_template("dashboard.html")
    #if session.get('username'):
    #    return 'Welcome to PlantSpeak, %s!' % session['username']
    #return 'Welcome to PlantSpeak!'
