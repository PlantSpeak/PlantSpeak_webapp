from flask import Blueprint, current_app, url_for, request, redirect, render_template, session

main_pages = Blueprint('main', __name__, template_folder="views")
@main_pages.route('/')
def home():
    return redirect(url_for('plants.dashboard'))
