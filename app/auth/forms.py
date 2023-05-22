from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from app.models import User


class LoginForm(FlaskForm):
    identifier = StringField('Username or Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()],id="username")
    email = StringField('Email', validators=[DataRequired(), Email()],id="email")
    password = PasswordField('Password', validators=[DataRequired()],id="password")
    confirm_password = PasswordField(
        'Confirm Password', validators=[DataRequired(), EqualTo('password')],id="confirm_password")
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')


class ResetPasswordForm(FlaskForm):
    old_password = PasswordField('Old Password :', validators=[DataRequired()], id="old_password")
    password = PasswordField('New Password :', validators=[DataRequired()], id="new_password")
    confirm_password = PasswordField(
        'Confirm Password :', validators=[DataRequired(), EqualTo('password')], id="confirm_password")
    submit = SubmitField('Change Password')
