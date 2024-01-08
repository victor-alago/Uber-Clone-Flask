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


user_auth_bp = Blueprint("user_authentication", __name__, template_folder="templates")

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

# Create User Table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
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
                role TEXT DEFAULT 'user'
            )
        ''')
conn.commit()
conn.close()


def get_db_connection():
    conn = sqlite3.connect(UBER_DB)
    conn.row_factory = sqlite3.Row
    return conn

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired()]) 
    first_name = StringField('First Name', validators=[InputRequired()])
    last_name = StringField('Last Name', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6)])
    age = IntegerField('Age', validators=[InputRequired(), NumberRange(min=18, max=90, message='User must be at least 18 years old')])
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])
    remember = BooleanField('Remember Me') 
    submit = SubmitField('Login')



@user_auth_bp.route('/user_register', methods=['GET', 'POST'])
def user_register():
    form = RegistrationForm()
    if form.validate_on_submit():
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if the email already exists in the database
        cursor.execute('SELECT * FROM users WHERE email = ?', (form.email.data,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash('Email already exists. Please use a different email.')
            return redirect(url_for('user_authentication.user_login'))
        else:
            hashed_password = generate_password_hash(form.password.data)

            cursor.execute('INSERT INTO users (email, first_name, last_name, password, age) VALUES (?, ?, ?, ?, ?)',
                           (form.email.data, form.first_name.data, form.last_name.data, hashed_password, form.age.data))
            conn.commit()
            conn.close()
            flash('Registration successful. Please log in.')
            return redirect(url_for('user_authentication.user_login'))

    return render_template('user_register.html', form=form)



@user_auth_bp.route('/user_login', methods=['GET', 'POST'])
def user_login():
    form = LoginForm()
    if form.validate_on_submit():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (form.email.data,))
        user_record = cursor.fetchone()
        conn.close()
        if user_record and check_password_hash(user_record['password'], form.password.data):
            user = User(user_record['id'], user_record['email'], 'user') # Create a User object
            login_user(user, remember=form.remember.data)
            flash("Logged in successfully")
            return redirect(url_for('user_dashboard.user_home'))
        else:
            flash('Invalid email or password')
    return render_template('user_login.html', form=form)


@user_auth_bp.route('/logout')
@login_required
def logout():
    logout_user()  
    flash('You have been logged out.')
    return redirect(url_for('user_authentication.user_login'))

@login_manager.user_loader
def load_user(user_id):
    """
    Given a user_id, return the corresponding user object.
    """
    # Establish database connection
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Query the database for user data based on the id
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user_record = cursor.fetchone()
    
    # Close the connection
    conn.close()
    
    # Check if user record exists
    if user_record:
        # Return an instance of the User class
        return User(id=user_record['id'], email=user_record['email'], role=user_record['role'])
    else:
        # Return None if no user is found
        return None
