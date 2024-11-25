# IMPORTS
from flask import Blueprint, render_template, flash, redirect, url_for, session, request
from flask_login import login_user, current_user, logout_user, login_required
from markupsafe import Markup
from app import db, roles_required
from models import User
from users.forms import RegisterForm, LoginForm
from datetime import datetime
import logging
import bcrypt
import pyotp

# CONFIG
users_blueprint = Blueprint('users', __name__, template_folder='templates')


# VIEWS
# view registration
@users_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    # create signup form object
    form = RegisterForm()

    # if request method is POST or form is valid
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        # if this returns a user, then the email already exists in database

        # if email already exists redirect user back to signup page with error message so user can try again
        if user:
            flash('Email address already exists')
            return render_template('users/register.html', form=form)
        # logs a new user registration
        logging.warning('SECURITY - User registration [%s, %s]', form.email.data, request.remote_addr)

        # create a new user with the form data
        new_user = User(email=form.email.data,
                        firstname=form.firstname.data,
                        lastname=form.lastname.data,
                        phone=form.phone.data,
                        password=form.password.data,
                        role='user')

        # add the new user to the database
        db.session.add(new_user)
        db.session.commit()

        # sends user to login page
        return redirect(url_for('users.login'))
    # if request method is GET or form not valid re-render signup page
    return render_template('users/register.html', form=form)


# view user login
@users_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    # initialises a key-value pair to keep track of the number of login attempts
    if not session.get('authentication_attempts'):
        session['authentication_attempts'] = 0
    # create login form object
    form = LoginForm()

    # if request method is POST or form is valid
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if not user \
                or not bcrypt.checkpw(form.password.data.encode('utf-8'), user.password) \
                or not pyotp.TOTP(user.pinkey).verify(form.pin.data):
            # if the data input by the form is not a real user or the password or time based pin doesn't match runs code
            # below
            # logs invalid log in attempt
            logging.warning('SECURITY - Invalid Login Attempt [%s, %s]', form.email.data, request.remote_addr)
            # increases the number of authentication attempts stored by session by 1 for failed login attempt
            session['authentication_attempts'] += 1
            # if the user has exceeded the maximum number of failed login attempts(3) blocks the user from logging in
            # by not passing a form to the html and provides a valid error message with a link to reset login attempts
            if session.get('authentication_attempts') >= 3:
                flash(Markup('Number of incorrect login attempts exceeded. Please click '
                             '<a href="/reset">here</a> to reset.'))
                return render_template('users/login.html')
            # if the user has not exceeded the login attempts provides an error message to let the user know the login
            # failed and how many attempts they have left to login before being locked out
            flash('Please check your login details and try again, {} login attempts remaining'
                  .format(3 - session.get('authentication_attempts')))
            return render_template('users/login.html', form=form)
        else:
            # if the users credentials are correct log's in the user and updates value of users last login in database
            login_user(user)
            user.last_login = user.current_login
            user.current_login = datetime.now()
            db.session.add(user)
            db.session.commit()
            # logs successful login attempt
            logging.warning('SECURITY - Log in [%d, %s, %s]', current_user.id, current_user.email, request.remote_addr)
            # redirects user to page depending on their role after logging in
            if current_user.role == 'user':
                return redirect(url_for('users.profile'))
            if current_user.role == 'admin':
                return redirect(url_for('admin.admin'))
    # if request method is GET or form is not valid re-render login page
    return render_template('users/login.html', form=form)


# resets the number of login attempts and reloads the user.login page
@users_blueprint.route('/reset')
def reset():
    session['authentication_attempts'] = 0
    return redirect(url_for('users.login'))


# logs the current user out and redirects anonymous user to home page
@users_blueprint.route('/logout')
@login_required
@roles_required('admin', 'user')
def logout():
    logging.warning('SECURITY - Log Out [%d, %s, %s]', current_user.id, current_user.email, request.remote_addr)
    logout_user()
    return redirect(url_for('index'))


# view user profile
@users_blueprint.route('/profile')
@login_required
@roles_required('user')
def profile():
    return render_template('users/profile.html', name=current_user.firstname)


# view user account
@users_blueprint.route('/account')
@login_required
@roles_required('admin', 'user')
def account():
    return render_template('users/account.html',
                           acc_no=current_user.id,
                           email=current_user.email,
                           firstname=current_user.firstname,
                           lastname=current_user.lastname,
                           phone=current_user.phone)
