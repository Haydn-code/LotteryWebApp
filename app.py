# IMPORTS
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import current_user, LoginManager
from dotenv import load_dotenv
from functools import wraps
from flask_talisman import Talisman
import logging
import os


# defines a filter class that will only return logged messages with the string SECURITY in
class SecurityFilter(logging.Filter):
    def filter(self, record):
        return 'SECURITY' in record.getMessage()


# provides access to the root logger to interact with
logger = logging.getLogger()
# opens a log file(if doesn't exist creates log file) to write logs too
file_handler = logging.FileHandler('lottery.log', 'a')
# only writes logs of level warning and below to the file handler
file_handler.setLevel(logging.WARNING)
# filters through the logs so that only logs containing the keyword SECURITY will be written to the file
file_handler.addFilter(SecurityFilter())
# defines a formatter that defines the format in which logs will be displayed through
formatter = logging.Formatter('%(asctime)s : %(message)s', '%m/%d/%Y %I:%M:%S %p')
# assigns the formatter to the file handler so that logs will be displayed in the layout provided by the formatter
file_handler.setFormatter(formatter)
# adds the file handler to the root logger so that the route logger will send the appropriate log messages to it
logger.addHandler(file_handler)

# loads data from env file to be accessed
load_dotenv()

# CONFIG
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_ECHO'] = os.getenv('SQLALCHEMY_ECHO') == 'True'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS') == 'True'
app.config['RECAPTCHA_PUBLIC_KEY'] = os.getenv('RECAPTCHA_PUBLIC_KEY')
app.config['RECAPTCHA_PRIVATE_KEY'] = os.getenv('RECAPTCHA_PRIVATE_KEY')

# initialise database
db = SQLAlchemy(app)

# added a custom security policy which whitelists certain sites and features within the lottery app so that they aren't
# blocked by the default security headers
csp = {
    'default-src': ['\'self\'', 'https://cdnjs.cloudflare.com/ajax/libs/bulma/0.7.2/css/bulma.min.css'],
    'frame-src': ['\'self\'', 'https://www.google.com/recaptcha/', 'https://recaptcha.google.com/recaptcha/'],
    'script-src': ['\'self\'', '\'unsafe-inline\'', 'https://www.google.com/recaptcha/',
                   'https://www.gstatic.com/recaptcha/']
}

# adds default security headers to http protocol with whitelisted sites defined in my custom security policy
# adds permissions policy to prevent 3rd parties from tracking user session
talisman = Talisman(app, content_security_policy=csp, permissions_policy="interest-cohort=()")
# prevents website from blocking itself since it runs on http
talisman.force_https = False


# defined my own custom wrapper function which takes authorised roles as a parameter and redirects the user to the
# forbidden error page if they do not have access to the page
def roles_required(*roles):
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if current_user.role not in roles:
                # logs logged on users attempting to access pages they don't have access too
                logging.warning("SECURITY - Invalid access attempts [%d, %s, %s, %s]", current_user.id,
                                current_user.email, current_user.role, request.remote_addr)
                return render_template('errors/403.html')
            return f(*args, **kwargs)

        return wrapped

    return wrapper


# HOME PAGE VIEW
@app.route('/')
def index():
    return render_template('main/index.html')


# directs errors in the app to custom error pages
@app.errorhandler(400)
def bad_request_error(error):
    return render_template('errors/400.html')


@app.errorhandler(403)
def forbidden_error(error):
    return render_template('errors/403.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html')


@app.errorhandler(500)
def internal_server_error(error):
    return render_template('errors/500.html')


@app.errorhandler(503)
def service_unavailable_error(error):
    return render_template('errors/503.html')


# BLUEPRINTS
# import blueprints
from users.views import users_blueprint
from admin.views import admin_blueprint
from lottery.views import lottery_blueprint

#
# # register blueprints with app
app.register_blueprint(users_blueprint)
app.register_blueprint(admin_blueprint)
app.register_blueprint(lottery_blueprint)

from models import User

# defines a login manager that sets a base page to send anonymous users
login_manager = LoginManager()
login_manager.login_view = 'user.login'
login_manager.init_app(app)


# loads instance of user from database
@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


if __name__ == "__main__":
    app.run()
