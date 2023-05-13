from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime as dt
from sqlalchemy import func

from .aiapi import generateChatResponse
from .extensions import db
from .models import User, GameQuestions, GameAnswers, Quiz

main = Blueprint('main', __name__)



@main.route('/generate-quiz', methods=['POST'])
def generate_quiz():
    if 'user_id' in session:
        user_id = session['user_id']
    else:
        return "User not logged in", 401

    current_datetime = dt.now()

    prompt = request.form['prompt']
    res = generateChatResponse(prompt)

    quiz_number = (
        db.session.query(func.max(Quiz.quiz_number))
        .filter_by(user_id=user_id)
        .scalar()
    )
    if quiz_number is None:
        quiz_number = 1
    else:
        quiz_number += 1

    quiz = Quiz(user_id=user_id, datetime=current_datetime, quiz_number=quiz_number)
    db.session.add(quiz)
    db.session.commit()

    for i, question_text in enumerate(res['question_text'], start=1):
        question = GameQuestions(
            user_id=user_id,
            datetime=current_datetime,
            quiz_number=quiz_number,
            question_number=i,
            question_text=question_text,
            quiz_id=quiz.id
        )
        db.session.add(question)
        db.session.commit()

        answer_options = res['answer_options']
        answer_options_per_question = answer_options[(i - 1) * 4: i * 4]

        for j, (option_letter, option_text) in enumerate(answer_options_per_question, start=1):
            if res['correct_answer']:
                correct_answer_option = ord(res['correct_answer'][i - 1].lower()) - ord('a') + 1
                correct_answer = (j == correct_answer_option)
            else:
                correct_answer = False

            answer = GameAnswers(
                user_id=user_id,
                datetime=current_datetime,
                quiz_id=quiz.id,
                question_id=question.id,
                answer_letter=option_letter,
                answer_text=option_text,
                correct_answer=correct_answer
            )
            db.session.add(answer)
            db.session.commit()

    quiz_url = f"/user-{user_id}-quiz-{quiz_number}"
    return jsonify({"quiz_number": quiz_number, "quiz_url": quiz_url}), 200


@main.route('/user-<int:user_id>-quiz-<int:quiz_number>', methods=['GET'])
def quiz_page(user_id, quiz_number):
    if 'user_id' in session:
        if session['user_id'] == user_id:
            quiz = Quiz.query.filter_by(user_id=user_id, quiz_number=quiz_number).first()
            if quiz is None:
                return "Quiz not found", 404

            questions = GameQuestions.query.filter_by(user_id=user_id, quiz_number=quiz_number).all()
            if not questions:
                return "No questions found for the quiz", 404

            return render_template('generated-quiz.html', quiz=quiz, questions=questions)

    return "Unauthorized", 401


@main.route('/quiz', methods=['GET', 'POST'])
def quiz_view():
    if request.method == 'POST':
        if 'user_id' in session:
            user_id = session['user_id']  # Get the user_id from the session
        else:
            return "User not logged in", 401

        current_datetime = dt.now()  # Set the datetime value

        prompt = request.form['prompt']
        res = generateChatResponse(prompt)

        # Determine the quiz_number for the user
        quiz_number = (
            db.session.query(func.max(Quiz.quiz_number))
            .filter_by(user_id=user_id)
            .scalar()
        )
        if quiz_number is None:
            quiz_number = 1
        else:
            quiz_number += 1

        # Create a new Quiz object
        quiz = Quiz(user_id=user_id, datetime=current_datetime, quiz_number=quiz_number)
        db.session.add(quiz)
        db.session.commit()

        for i, question_text in enumerate(res['question_text'], start=1):
            question = GameQuestions(
                user_id=user_id,
                datetime=current_datetime,
                quiz_number=quiz_number,
                question_number=i,
                question_text=question_text,
                quiz_id=quiz.id
            )
            db.session.add(question)
            db.session.commit()

            answer_options = res['answer_options']
            answer_options_per_question = answer_options[(i - 1) * 4: i * 4]  # Get the answer options for the current question

            for j, (option_letter, option_text) in enumerate(answer_options_per_question, start=1):
                if res['correct_answer']:
                    correct_answer_option = ord(res['correct_answer'][i - 1].lower()) - ord('a') + 1
                    correct_answer = (j == correct_answer_option)
                else:
                    correct_answer = False

                answer = GameAnswers(
                    user_id=user_id,
                    datetime=current_datetime,
                    quiz_id=quiz.id,
                    question_id=question.id,  # Use the question's ID
                    answer_letter=option_letter,
                    answer_text=option_text,
                    correct_answer=correct_answer
                )
                db.session.add(answer)
                db.session.commit()

        return jsonify(res), 200

    return render_template('quiz.html')

@main.route('/')
def index():
    return render_template('landing.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form['identifier'].lower()  # Convert identifier to lowercase
        password = request.form['password']
        user = User.query.filter(db.or_(func.lower(User.email) == identifier, func.lower(User.username) == identifier)).first()  # Use func.lower to convert email and username to lowercase

        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            flash('You have been logged in!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Username or password is incorrect', 'danger')

    return render_template('login.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']  # Add username field
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('main.register'))

        existing_user = User.query.filter(db.or_(User.email == email, User.username == username)).first()
        if existing_user:
            flash('Email address or username already in use', 'danger')
            return redirect(url_for('main.register'))

        new_user = User(username=username, email=email, password=password)  # Add username field
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

@main.route('/account', methods=['GET', 'POST'])
def account():
    user_id = session.get('user_id')
    if not user_id:
        flash('You need to be logged in to access your account.', 'danger')
        return redirect(url_for('main.login'))

    user = User.query.get(user_id)

    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if not check_password_hash(user.password_hash, old_password):
            flash('Incorrect old password. Please try again.', 'danger')
            return redirect(url_for('main.account'))

        if new_password != confirm_password:
            flash('New password and confirm password do not match.', 'danger')
            return redirect(url_for('main.account'))

        user.password_hash = generate_password_hash(new_password)
        db.session.commit()

        flash('Password changed successfully! Please log in with your new password.', 'success')
        session.clear()  # Clear the session to log the user out
        return redirect(url_for('main.login'))

    return render_template('account.html', user=user)





@main.route('/dashboard')
def dashboard():
    if not session.get('user_id'):
        flash('You must be logged in to access the dashboard', 'warning')
        return redirect(url_for('main.login'))

    return render_template('dashboard.html')
