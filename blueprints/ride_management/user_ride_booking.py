from flask import Blueprint, render_template, redirect, request, url_for
from flask_login import login_required, current_user
from blueprints.dashboards.user_dashboard import get_db_connection
import os
from pymongo import MongoClient
import uuid


user_rides_bp = Blueprint("user_rides", __name__, template_folder="templates")

mongo_client = MongoClient('mongodb://localhost:27017/')
db = mongo_client['uber_clone_db']  # Database name: uber_clone_db
rides_collection = db['rides']  # Collection name: rides


UBER_DB = os.environ.get("UBER_DB")


@user_rides_bp.route('/submit_ride_details', methods=['POST'])
@login_required
def submit_ride_details():
    # Capture form data
    pickup_location = request.form.get('pickupLocation')
    dropoff_location = request.form.get('dropOffLocation')
    pickup_time = request.form.get('pickupTime')
    car_type = request.form.get('carType')

    # Get user data (modify as per your user data retrieval method)
    user_info = {}
    # available_cars = {}
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT email, first_name, last_name, age, profile_pic FROM users WHERE id = ?', (current_user.id,))
        user_info = cursor.fetchone()


    # Render user_ride_booking.html with the data
    return render_template('user_ride_booking.html', booking={
        'user_name': user_info['first_name'] + ' ' + user_info['last_name'],
        'pickup_address': pickup_location,
        'drop_off_address': dropoff_location,
        'pickup_time': pickup_time,
        'car_type': car_type,
    }, user=user_info)



@user_rides_bp.route('/request_ride', methods=['POST'])
@login_required
def request_ride():
    ride_id = uuid.uuid4().hex

    ride_details = {
        "ride_id": ride_id,
        "user_id": current_user.id,
        "user_name": request.form.get('user_name'),
        "pickup_address": request.form.get('pickup_address'),
        "drop_off_address": request.form.get('drop_off_address'),
        "pickup_time": request.form.get('pickup_time'),
        "car_type": request.form.get('car_type'),
        "status": "awaiting_driver"
    }

    # Store data in MongoDB
    rides_collection.insert_one(ride_details)
    ride_id = ride_details['ride_id']

    return redirect(url_for('user_rides.waiting_for_driver', ride_id=ride_id))

@user_rides_bp.route('/waiting_for_driver')
@login_required
def waiting_for_driver():
    ride_id = request.args.get('ride_id')
    user_id = current_user.id
    return render_template('waiting_for_driver.html', ride_id=ride_id, user_id=user_id)


@user_rides_bp.route('/check_ride_status')
@login_required
def check_ride_status():
    ride_id = request.args.get('ride_id')
    ride = rides_collection.find_one({"ride_id": ride_id})
    if ride and ride.get('status') == 'accepted':
        return {"driver_accepted": True, "user_id": ride['user_id']}
    else:
        return {"driver_accepted": False}



