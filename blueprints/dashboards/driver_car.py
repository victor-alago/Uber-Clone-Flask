from dotenv import load_dotenv
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_from_directory
from flask_login import LoginManager, login_required, current_user
from flask_wtf import FlaskForm
from werkzeug.utils import secure_filename
from wtforms import SubmitField, FileField, StringField
from blueprints.authentication.driver_auth import User
import sqlite3
import os
from PIL import Image
import secrets

driver_car_bp = Blueprint('driver_car', __name__, template_folder='templates')

load_dotenv()
UBER_DB = os.environ.get("UBER_DB")

# Database Initialization
conn = sqlite3.connect(UBER_DB)
cursor = conn.cursor()


cursor.execute('''
    CREATE TABLE IF NOT EXISTS cars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                driver_id INTEGER,
                type TEXT,
                make TEXT,
                model TEXT,
                year INTEGER,
                seater INTEGER,
                color TEXT,
                plate_number TEXT,
                car_picture TEXT DEFAULT NULL,
                FOREIGN KEY (driver_id) REFERENCES drivers(id)
            )
        ''')
conn.commit()
conn.close()

class CarForm(FlaskForm):
    type = StringField('Car Type')
    make = StringField('Car Make')
    model = StringField('Car Model')
    year = StringField('Car Year')
    seater = StringField('Car Seater')
    color = StringField('Car Color')
    plate_number = StringField('Car Plate Number')
    car_picture = FileField('Car Picture')
    submit = SubmitField('Update Car')


def get_db_connection():
    conn = sqlite3.connect(current_app.config['UBER_DB'])
    conn.row_factory = sqlite3.Row
    return conn


def save_car_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/car_pics', picture_fn)

    output_size = (300, 300)  
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


def delete_car_picture(filename):
    file_path = os.path.join(current_app.root_path, 'static/car_pics', filename)
    if os.path.exists(file_path):
        os.remove(file_path)


def get_car_info():
    car_info = {}
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM cars WHERE driver_id = ?', (current_user.id,))
        car_info = cursor.fetchone()
        return car_info


@driver_car_bp.route('/driver_car', methods=['GET', 'POST'])
@login_required
def driver_car():
    form = CarForm()
    if form.validate_on_submit():
        car_picture_file = save_car_picture(form.car_picture.data) if form.car_picture.data else None
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if car_picture_file:
                cursor.execute('UPDATE cars SET car_picture = ? WHERE driver_id = ?', (car_picture_file, current_user.id))
            cursor.execute('UPDATE cars SET type = ?, make = ?, model = ?, year = ?, seater = ?, color = ?, plate_number = ? WHERE driver_id = ?', 
                           (form.type.data, form.make.data, form.model.data, form.year.data, form.seater.data, form.color.data, form.plate_number.data, current_user.id))
            conn.commit()
        flash('Car details updated!', 'success')
        return redirect(url_for('driver_car.driver_car'))

    car_info = get_car_info()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT type, make, model, year, seater, color, plate_number, car_picture FROM cars WHERE driver_id = ?', (current_user.id,))
        car_info = cursor.fetchone()

    car_pic_url = url_for('static', filename='car_pics/' + car_info['car_picture']) if car_info and car_info['car_picture'] else url_for('static', filename='car_pics/default_car.jpg')
    return render_template('driver_car.html', title='Driver-Car', form=form, car=car_info, car_pic_url=car_pic_url)