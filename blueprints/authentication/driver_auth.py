from flask import Blueprint, render_template, redirect, url_for, flash, session, current_app
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField
from wtforms.validators import InputRequired, Length, Email, NumberRange
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from dotenv import load_dotenv
import os
from extensions import login_manager


driver_auth_bp = Blueprint("driver_authentication", __name__, template_folder="templates")

load_dotenv()
UBER_DB = os.environ.get("UBER_DB")


# Define the User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, email, role):
        self.id = id
        self.email = email
        self.role = role


# Database Initialization
conn = sqlite3.connect(UBER_DB)
cursor = conn.cursor()

# Create Driver Table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS drivers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE,
                first_name TEXT,
                last_name TEXT,
                password TEXT,
                age INTEGER,
                country TEXT DEFAULT NULL,
                zip_code TEXT DEFAULT NULL,
                city TEXT DEFAULT NULL,
                profile_pic TEXT DEFAULT NULL,
                role TEXT DEFAULT 'driver'
    )
''')
conn.commit()
conn.close()

def get_db_connection():
    conn = sqlite3.connect(UBER_DB)
    conn.row_factory = sqlite3.Row
    return conn


class DriverRegistrationForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired()])
    first_name = StringField('First Name', validators=[InputRequired()])
    last_name = StringField('Last Name', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6)])
    age = IntegerField('Age', validators=[InputRequired(), NumberRange(min=21, max=90, message='Driver must be at least 21 years old with 3 years experience')])
    submit = SubmitField('Register')


class DriverLoginForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])
    remember = BooleanField('Remember Me') 
    submit = SubmitField('Login')



@driver_auth_bp.route('/driver_register', methods=['GET', 'POST'])
def driver_register():
    form = DriverRegistrationForm()
    if form.validate_on_submit():
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if the email already exists in the database
        cursor.execute('SELECT * FROM drivers WHERE email = ?', (form.email.data,))
        existing_driver = cursor.fetchone()

        if existing_driver:
            flash('Email already exists. Please use a different email.')
            return redirect(url_for('driver_authentication.driver_login'))
        else:
            hashed_password = generate_password_hash(form.password.data)

            cursor.execute('INSERT INTO drivers (email, first_name, last_name, password, age) VALUES (?, ?, ?, ?, ?)',
                           (form.email.data, form.first_name.data, form.last_name.data, hashed_password, form.age.data))
            driver_id = cursor.lastrowid  # Get the ID of the new driver
            # Insert new car record for the new driver into cars table
            cursor.execute('INSERT INTO cars (driver_id) VALUES (?)', (driver_id,))
            conn.commit()
            conn.close()
            flash('Registration successful. Please log in.')
            return redirect(url_for('driver_authentication.driver_login'))

    return render_template('driver_register.html', form=form)


@driver_auth_bp.route('/driver_login', methods=['GET', 'POST'])
def driver_login():
    form = DriverLoginForm()
    if form.validate_on_submit():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM drivers WHERE email = ?', (form.email.data,))
        driver_record = cursor.fetchone()
        conn.close()
        if driver_record and check_password_hash(driver_record['password'], form.password.data):
            driver = User(driver_record['id'], driver_record['email'], 'driver')
            login_user(driver, remember=form.remember.data)
            # session['driver_id'] = driver['id']  # Store driver ID in session
            flash("Logged in successfully")
            return redirect(url_for('driver_dashboard.driver_home')) 
        else:
            flash('Invalid email or password')
            
    return render_template('driver_login.html', form=form)



@driver_auth_bp.route('/driver_logout')
@login_required
def driver_logout(): 
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('driver_authentication.driver_login'))

@login_manager.user_loader
def load_user(driver_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM drivers WHERE id = ?', (driver_id,))
    driver_record = cursor.fetchone()

    conn.close()
    
    # Check if user record exists
    if driver_record:
        return User(id=driver_record['id'], email=driver_record['email'], role=driver_record['role'])
    else:
        return None
