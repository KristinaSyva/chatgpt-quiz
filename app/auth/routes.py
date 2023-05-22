from flask import Blueprint, render_template, flash, \
    redirect, url_for

from sqlalchemy import func
from flask_login import current_user, login_user, logout_user, login_required
from app.extensions import db
from app.models import User
from .forms import LoginForm, RegistrationForm, ResetPasswordForm

auth = Blueprint('auth', __name__)


@auth.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('auth/landing.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        # Use func.lower to convert email and username to lowercase
        user = User.query.filter(db.or_(func.lower(User.email) == form.identifier.data.lower(), func.lower(
            User.username) == form.identifier.data.lower())).first()

        if user and user.check_password(form.password.data):
            login_user(user)
            flash('You have been logged in!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Username or password is incorrect', 'error')

    return render_template('auth/login.html', form=form)


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        flash('Registration successful. You can now login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))


@auth.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    form = ResetPasswordForm()
    user_id = current_user.id
    user = User.query.get(user_id)

    if form.validate_on_submit():
        if not user.check_password(form.old_password.data):
            flash('Incorrect old password. Please try again.', 'error')
            return redirect(url_for('auth.account'))

        user.set_password(form.password.data)
        db.session.commit()

        flash('Password changed successfully! Please log in with your new password.', 'success')
        logout_user()
        return redirect(url_for('auth.login'))
    return render_template('auth/account.html', user=user, form=form)
