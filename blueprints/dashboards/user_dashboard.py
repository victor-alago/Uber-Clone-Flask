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


user_dashboard_bp = Blueprint('user_dashboard', __name__, template_folder='templates')

UBER_DB = os.environ.get("UBER_DB")

def get_db_connection():
    conn = sqlite3.connect(UBER_DB)
    conn.row_factory = sqlite3.Row
    return conn


class UserPictureForm(FlaskForm):
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

@user_dashboard_bp.route('/profile_pics/<filename>')
def profile_picture(filename):
    return send_from_directory('static/profile_pics', filename)

@user_dashboard_bp.route('/user_home')
@login_required
def user_home():
    user_info = {}
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT email, first_name, last_name, age, profile_pic FROM users WHERE id = ?', (current_user.id,))
        user_info = cursor.fetchone()
    return render_template('user_home.html', user=user_info)

@user_dashboard_bp.route('/user_profile', methods=['GET', 'POST'])
@login_required
def user_profile():
    form = UserPictureForm()
    if form.validate_on_submit():
        picture_file = save_picture(form.profile_pic.data) if form.profile_pic.data else None
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if picture_file:
                cursor.execute('UPDATE users SET profile_pic = ? WHERE id = ?', (picture_file, current_user.id))
            cursor.execute('UPDATE users SET email = ?, first_name = ?, last_name = ?, age = ?, country = ?, zip_code = ?, city = ? WHERE id = ?',
                           (form.email.data, form.first_name.data, form.last_name.data, form.age.data, form.country.data, form.zip_code.data, form.city.data, current_user.id))
            conn.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('user_dashboard.user_profile'))

    user_info = {}
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT email, first_name, last_name, age, country, zip_code, city, profile_pic FROM users WHERE id = ?', (current_user.id,))
        user_info = cursor.fetchone()

    profile_pic_url = url_for('static', filename='profile_pics/' + user_info['profile_pic']) if user_info and user_info['profile_pic'] else url_for('static', filename='profile_pics/default.jpg')
    return render_template('user_profile.html', title='Account', form=form, user=user_info, profile_pic_url=profile_pic_url)

@user_dashboard_bp.route('/delete_user_profile_pic', methods=['POST'])
@login_required
def delete_user_profile_pic():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT profile_pic FROM users WHERE id = ? and role = ?', (current_user.id, 'user'))
        user = cursor.fetchone()
        if user and user['profile_pic']:
            delete_picture(user['profile_pic'])
            cursor.execute('UPDATE users SET profile_pic = NULL WHERE id = ? and role = ?', (current_user.id, 'user'))
            conn.commit()
        flash('Profile picture deleted!', 'success')
    return redirect(url_for('user_dashboard.user_profile'))
