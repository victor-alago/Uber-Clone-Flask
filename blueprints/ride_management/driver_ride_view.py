from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from pymongo import MongoClient
from bson import ObjectId
from bson.errors import InvalidId
import sqlite3
import os

driver_rides_bp = Blueprint("driver_rides", __name__, template_folder="templates")

# Setup MongoDB connection
mongo_client = MongoClient('mongodb://localhost:27017/')
db = mongo_client['uber_clone_db']
rides_collection = db['rides']


UBER_DB = os.environ.get("UBER_DB")
def get_db_connection():
    conn = sqlite3.connect(UBER_DB)
    conn.row_factory = sqlite3.Row
    return conn


@driver_rides_bp.route('/view_ride_details', methods=['POST'])
@login_required
def view_ride_details():
    ride_id = request.form.get('ride_id')

    if not ride_id:
        flash('Invalid Ride ID.', 'error')
        return redirect(url_for('driver_dashboard.driver_home'))

    ride_details = rides_collection.find_one({"ride_id": ride_id})
    if ride_details is None:
        flash('Ride not found.', 'error')
        return redirect(url_for('driver_dashboard.driver_home'))
    return render_template('driver_ride_view.html', ride=ride_details, ride_id=ride_id)



@driver_rides_bp.route('/accept_ride/<ride_id>')
@login_required
def accept_ride(ride_id):
    driver_info = {}
    car_info = {}
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT email, first_name, last_name, age, profile_pic FROM drivers WHERE id = ?', (current_user.id,))
        driver_info = cursor.fetchone()
        cursor.execute('SELECT * FROM cars WHERE driver_id = ?', (current_user.id,))
        car_info = cursor.fetchone()

    print(f"Driver Info: {driver_info}")
    print(f"Car Info: {car_info}")
    print(f"Ride ID: {ride_id}")

    # Update the ride in the database with driver's details
    update_data = {
        "status": "accepted",
        "driver_details": {
            "driver_id": current_user.id,
            "name": f"{driver_info['first_name']} {driver_info['last_name']}",
            "email": driver_info['email'],
            # "profile_pic": driver_info['profile_pic']
        },
        "car_details": {
            "car_type": car_info['type'],
            "plate_number": car_info['plate_number'],

        }
    }
    # Update the ride in the MongoDB database

    result = rides_collection.update_one(
        {"ride_id": ride_id, "status": "awaiting_driver"},
        {"$set": update_data}
    )

    # ride_id = request.args.get('ride_id') 
    if result.modified_count > 0:
        flash('Ride accepted.', 'success')
        return redirect(url_for('chat.chat', ride_id=ride_id, driver_id=current_user.id))
    else:
        flash('No ride was updated. Please check if the ride ID is correct and the ride is awaiting a driver.', 'error')
        return redirect(url_for('driver_dashboard.driver_home'))




@driver_rides_bp.route('/decline_ride/<ride_id>')
@login_required
def decline_ride(ride_id):
    flash('Ride declined.', 'info')
    return redirect(url_for('driver_dashboard.driver_home'))
