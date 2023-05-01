from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import check_password_hash


from .aiapi import generateChatResponse
from .extensions import db
from .models import User, Quiz

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('landing.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            flash('You have been logged in!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Email or password is incorrect', 'danger')

    return render_template('login.html')


@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('main.register'))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email address already in use', 'danger')
            return redirect(url_for('main.register'))

        new_user = User(email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful. You can now login.', 'success')
        return redirect(url_for('main.login'))

    return render_template('register.html')


@main.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.index'))


@main.route('/dashboard')
def dashboard():
    if not session.get('user_id'):
        flash('You must be logged in to access the dashboard', 'warning')
        return redirect(url_for('main.login'))

    return render_template('dashboard.html')


@main.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if request.method == 'POST':
        prompt = request.form['prompt']
        res = {}
        res['answer'] = generateChatResponse(prompt)
        return jsonify(res), 200

    return render_template('quiz.html')

