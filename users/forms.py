from flask_wtf import FlaskForm, RecaptchaField
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Email, ValidationError, EqualTo
import re


# checks that an input field doesn't have any of the specified characters
def character_check(form, field):
    excluded_chars = "*?!'^+%&/()=}][{$#@<>"
    # iterates through excluded character list and checks against inputted data, if that character is found a validation
    # error is raised telling the user which inputted character wasn't allowed
    for char in field.data:
        if char in excluded_chars:
            raise ValidationError(f"Character {char} is not allowed.")


# checks that the data stored in input field matches XXXX-XXX-XXXX where X is an integer
def validate_phone(form, phone):
    p = re.compile(r"[0-9]{4}-[0-9]{3}-[0-9]{4}")
    # checks the phone data against the regex string to ensure correct format
    if not p.match(phone.data):
        raise ValidationError("Must be in format XXXX-XXX-XXXX where X is an integer")


# checks that the data stored in the input field contains a digit, a lowercase character, an uppercase character
# a special character and is between length 6 and 12
def validate_password(form, password):
    p = re.compile(r"(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*\W)^.{6,12}$")
    # checks the password data against the regex string to ensure correct format
    if not p.match(password.data):
        raise ValidationError("Must contain a digit(0-9), a lowercase character(a-z), an uppercase character(A-Z)"
                              "a special character(not 0-9, a-Z or _) and have a length between 6 and 12")


# creates a form that allows for the registration of new users(uses validators to check inputs)
class RegisterForm(FlaskForm):
    # a list of the input fields for users and the checks performed on each field
    email = StringField(validators=[DataRequired(), Email()])
    firstname = StringField(validators=[DataRequired(), character_check])
    lastname = StringField(validators=[DataRequired(), character_check])
    phone = StringField(validators=[DataRequired(), validate_phone])
    password = PasswordField(validators=[DataRequired(), validate_password])
    confirm_password = PasswordField(validators=[DataRequired(), EqualTo('password',
                                                                         message='Both password fields must be equal')])
    submit = SubmitField()


# creates a form that allows for the login of users(uses validators to check inputs)
class LoginForm(FlaskForm):
    email = StringField(validators=[DataRequired(), Email()])
    password = PasswordField(validators=[DataRequired()])
    pin = StringField(validators=[DataRequired()])
    recaptcha = RecaptchaField()
    submit = SubmitField()
