from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_from_directory
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from werkzeug.utils import secure_filename
from wtforms import StringField, SubmitField, FileField, IntegerField
from wtforms.validators import InputRequired, Email, NumberRange
import sqlite3
import os
from PIL import Image
import secrets
from pymongo import MongoClient



driver_dashboard_bp = Blueprint('driver_dashboard', __name__, template_folder='templates')


UBER_DB = os.environ.get("UBER_DB")
def get_db_connection():
    conn = sqlite3.connect(UBER_DB)
    conn.row_factory = sqlite3.Row
    return conn


mongo_client = MongoClient('mongodb://localhost:27017/')
db = mongo_client['uber_clone_db']
rides_collection = db['rides']



class DriverPictureForm(FlaskForm):
    profile_pic = FileField('Profile Picture')
    email = StringField('Email', validators=[InputRequired()])
    first_name = StringField('First Name', validators=[InputRequired()])
    last_name = StringField('Last Name', validators=[InputRequired()])
    age = IntegerField('Age', validators=[InputRequired(), NumberRange(min=18, max=100)])
    country = StringField('Country', validators=[InputRequired()])
    zip_code = StringField('Zip Code', validators=[InputRequired()])
    city = StringField('City', validators=[InputRequired()])
    submit = SubmitField('Update')




def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

def delete_picture(filename):
    file_path = os.path.join(current_app.root_path, 'static/profile_pics', filename)
    if os.path.exists(file_path):
        os.remove(file_path)

@driver_dashboard_bp.route('/profile_pics/<filename>')
def profile_picture(filename):
    return send_from_directory('static/profile_pics', filename)

@driver_dashboard_bp.route('/driver_home')
@login_required
def driver_home():
    driver_info = {}
    car_info = {}
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT email, first_name, last_name, age, profile_pic FROM drivers WHERE id = ?', (current_user.id,))
        driver_info = cursor.fetchone()
        cursor.execute('SELECT * FROM cars WHERE driver_id = ?', (current_user.id,))
        car_info = cursor.fetchone()

        ride_requests = list(rides_collection.find({}))


        for ride in ride_requests:
            ride['ride_id'] = str(ride['ride_id'])

        ride_requests = reversed(ride_requests)

    return render_template('driver_home.html', driver=driver_info, car=car_info, ride_requests=ride_requests)

@driver_dashboard_bp.route('/driver_profile', methods=['GET', 'POST'])
@login_required
def driver_profile():
    form = DriverPictureForm()
    if form.validate_on_submit():
        picture_file = save_picture(form.profile_pic.data) if form.profile_pic.data else None
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if picture_file:
                cursor.execute('UPDATE drivers SET profile_pic = ? WHERE id = ?', (picture_file, current_user.id))
            cursor.execute('UPDATE drivers SET email = ?, first_name = ?, last_name = ?, age = ?, country = ?, zip_code = ?, city = ? WHERE id = ?',
                           (form.email.data, form.first_name.data, form.last_name.data, form.age.data, form.country.data, form.zip_code.data, form.city.data, current_user.id))
            conn.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('driver_dashboard.driver_profile'))

    driver_info = {}
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT email, first_name, last_name, age, country, zip_code, city, profile_pic FROM drivers WHERE id = ?', (current_user.id,))
        driver_info = cursor.fetchone()

    profile_pic_url = url_for('static', filename='profile_pics/' + driver_info['profile_pic']) if driver_info and driver_info['profile_pic'] else url_for('static', filename='profile_pics/default.jpg')
    return render_template('driver_profile.html', title='Account', form=form, driver=driver_info, profile_pic_url=profile_pic_url)

@driver_dashboard_bp.route('/delete_driver_profile_pic', methods=['POST'])
@login_required
def delete_driver_profile_pic():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT profile_pic FROM drivers WHERE id = ? and role = ?', (current_user.id, 'driver'))
        driver = cursor.fetchone()
        if driver and driver['profile_pic']:
            delete_picture(driver['profile_pic'])
            cursor.execute('UPDATE drivers SET profile_pic = NULL WHERE id = ? and role = ?', (current_user.id, 'driver'))
            conn.commit()
        flash('Profile picture deleted!', 'success')
    return redirect(url_for('driver_dashboard.driver_profile'))


