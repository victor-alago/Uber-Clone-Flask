from datetime import datetime
from flask import Flask, Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_required, current_user
from blueprints.dashboards.user_dashboard import get_db_connection
from pymongo import MongoClient
import socketio



chat_bp = Blueprint('chat', __name__, template_folder='templates', static_folder='static')

# Setup MongoDB connection
mongo_client = MongoClient('mongodb://localhost:27017/')
db = mongo_client['uber_clone_db']
rides_collection = db['rides']



@chat_bp.route('/chat')
@chat_bp.route('/chat')
@login_required
def chat():
    ride_id = request.args.get('ride_id')
    
    # Fetch the ride details
    ride = rides_collection.find_one({"ride_id": ride_id})
    if not ride:
        flash("Ride not found.", "error")
        return redirect(url_for('chat.error_page'))

    print(f"Ride Info: {ride}")
    
    # Check if the current user is part of the ride
    is_driver = (current_user.id == ride.get('driver_details', {}).get('driver_id'))
    is_user = (current_user.id == ride.get('user_id'))

    if is_driver or is_user:
        return render_template('chat.html', user_id=ride['user_id'], driver_id=ride['driver_details'].get('driver_id'), ride_id=ride_id)
    else:
        flash("You're not authorized to view this chat.", "error")
        return redirect(url_for('chat.error_page'))


def check_if_driver(driver_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT role FROM drivers WHERE id = ?', (driver_id,))
        driver_data = cursor.fetchone()
        return driver_data and driver_data['role'] == 'driver'
    

@chat_bp.route('/invoice')
@login_required
def invoice():
    current_date = datetime.now().strftime("%B %d, %Y")
    return render_template('invoice.html', current_date=current_date)
   
@chat_bp.route('/error_page')
def error_page():
    return render_template('error.html')
