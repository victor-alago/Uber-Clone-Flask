from flask import Blueprint, render_template, current_app

admin_bp = Blueprint('admin_bp', __name__, template_folder='templates')

@admin_bp.route('/logs')
def logs():
    try:
        with open('app.log', 'r') as log_file:
            log_content = log_file.read()
        return render_template('logs.html', log_content=log_content)
    except IOError as e:
        # If there's an error, it will be printed in the console
        print(f"Error reading log file: {e}")
        return render_template('logs.html', log_content="No logs found.")

