import time
from flask import Flask, g, render_template
from flask_login import LoginManager
from dotenv import load_dotenv
import os

import socketio
from extensions import login_manager
from flask_socketio import SocketIO
from flask_socketio import emit, join_room, leave_room

from flask_debugtoolbar import DebugToolbarExtension
import logging
from logging.handlers import RotatingFileHandler
from werkzeug.middleware.profiler import ProfilerMiddleware

# Import blueprints and user classes
from blueprints.authentication.user_auth import user_auth_bp 
from blueprints.authentication.driver_auth import driver_auth_bp
from blueprints.dashboards.user_dashboard import user_dashboard_bp
from blueprints.dashboards.driver_dashboard import driver_dashboard_bp
from blueprints.dashboards.driver_car import driver_car_bp
from blueprints.ride_management.user_ride_booking import user_rides_bp
from blueprints.ride_management.driver_ride_view import driver_rides_bp
from blueprints.admin.logs import admin_bp


from blueprints.interactions.chat import chat_bp

app = Flask(__name__)
load_dotenv()
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
app.config['UBER_DB'] = os.environ.get("UBER_DB")
socketio = SocketIO(app)

# Set DEBUG_TB_INTERCEPT_REDIRECTS to False to avoid error
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
# Set DEBUG mode
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'False') == 'True'



toolbar = DebugToolbarExtension(app)


@socketio.on('join')
def on_join(data):
    room = data['user_id'] + '_' + data['driver_id']
    join_room(room)

@socketio.on('text')
def handle_text(data):
    room = data['sender_id'] + '_' + data['receiver_id']
    emit('message', {'msg': data['msg'], 'sender': data['sender_id']}, room=room)


# Initialize LoginManager
login_manager.init_app(app)

# Register blueprints
app.register_blueprint(user_auth_bp)
app.register_blueprint(driver_auth_bp)
app.register_blueprint(user_dashboard_bp)
app.register_blueprint(driver_dashboard_bp)
app.register_blueprint(driver_car_bp)
app.register_blueprint(user_rides_bp)
app.register_blueprint(driver_rides_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(chat_bp)




# Setup logging
#Logging could be disturbing the app
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=3)
handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)

@app.before_request
def before_request():
    g.start = time.time()

@app.after_request
def after_request(response):
    if 'start' in g:
        latency = time.time() - g.start
        app.logger.info(f"Request latency: {latency:.5f} seconds.")
    return response


# ProfilerMiddleware should be added only in debug mode and before starting the app
# Middle ware could be disturbing my flask app
if app.config['DEBUG']:
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, profile_dir='./profiles')


@app.route('/')
def index():
    app.logger.info('Homepage accessed')
    return render_template('index.html')

if __name__ == '__main__':
    socketio.run(app, debug=True)


