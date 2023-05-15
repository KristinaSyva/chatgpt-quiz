from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime as dt
from sqlalchemy import func

from .aiapi import generateChatResponse
from .extensions import db
from .models import User, GameQuestions, GameAnswers, Quiz

main = Blueprint('main', __name__)



@main.route('/user-<int:user_id>-quiz-<int:quiz_number>', methods=['GET'])
def quiz_page(user_id, quiz_number):
    if 'user_id' in session:
        if session['user_id'] == user_id:
            quiz = Quiz.query.filter_by(user_id=user_id, quiz_number=quiz_number).first()
            if quiz is None:
                return "Quiz not found", 404

            questions = GameQuestions.query.filter_by(quiz_id=quiz.id).all()
            if not questions:
                return "No questions found for the quiz", 404

            answer_options = []
            for question in questions:
                options = GameAnswers.query.filter_by(question_id=question.id).all()
                answer_options.extend(options)

            return render_template('generated-quiz.html', quiz=quiz, questions=questions, answer_options=answer_options)

    return "Unauthorized", 401



@main.route('/quiz', methods=['GET', 'POST'])
def quiz_view():
    if request.method == 'POST':
        if 'user_id' in session:
            user_id = session['user_id']
        else:
            return "User not logged in", 401

        prompt = request.form['prompt']
        res = generateChatResponse(prompt)

        # Store the quiz data in the session
        session['quiz_data'] = res
        #print("Generated Quiz Data:", res) 
        return jsonify(res), 200

    return render_template('quiz.html')


@main.route('/generate-quiz', methods=['POST'])
def generate_quiz():
    if 'user_id' in session:
        user_id = session['user_id']
    else:
        return "User not logged in", 401

    current_datetime = dt.now()

    # Retrieve the quiz data from the request
    res = session.get('quiz_data')
    
    print("Generated Quiz Data:", res) 

    if res is None:
        return "Quiz data not found in request", 400

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

    question_text = res['question_text']
    correct_answer = res['correct_answer']
    answer_options = res['answer_options']

    for i in range(len(question_text)):
        question = GameQuestions(
            user_id=user_id,
            datetime=current_datetime,
            quiz_number=quiz_number,
            question_number=i + 1,
            question_text=question_text[i],
            quiz_id=quiz.id
        )
        db.session.add(question)
        db.session.commit()

        answer_options_per_question = answer_options[i * 4: (i + 1) * 4]

        for j, (option_letter, option_text) in enumerate(answer_options_per_question, start=1):
            correct_answer_option = ord(correct_answer[i].lower()) - ord('a') + 1
            correct_answer_flag = (j == correct_answer_option)

            answer = GameAnswers(
                user_id=user_id,
                datetime=current_datetime,
                quiz_id=quiz.id,
                question_id=question.id,
                answer_letter=option_letter,
                answer_text=option_text,
                correct_answer=correct_answer_flag
            )
            db.session.add(answer)
            db.session.commit()

    return redirect(url_for('main.dashboard')) 



@main.route('/delete-quiz/<int:quiz_id>', methods=['GET', 'POST'])
def delete_quiz(quiz_id):
    if 'user_id' not in session:
        flash('You must be logged in to delete a quiz', 'warning')
        return redirect(url_for('main.login'))

    # Retrieve the quiz by ID
    quiz = Quiz.query.get(quiz_id)

    if not quiz:
        flash('Quiz not found', 'danger')
        return redirect(url_for('main.dashboard'))

    # Check if the logged-in user is the owner of the quiz
    if quiz.user_id != session['user_id']:
        flash('You are not authorized to delete this quiz', 'danger')
        return redirect(url_for('main.dashboard'))

    # Delete the associated GameQuestions and GameAnswers records
    game_questions = GameQuestions.query.filter_by(quiz_id=quiz.id).all()
    for question in game_questions:
        GameAnswers.query.filter_by(question_id=question.id).delete()
    GameQuestions.query.filter_by(quiz_id=quiz.id).delete()

    # Delete the quiz
    db.session.delete(quiz)
    db.session.commit()

    flash('Quiz deleted successfully', 'success')
    return redirect(url_for('main.dashboard'))


@main.route('/rename_quiz/<int:quiz_id>', methods=['POST'])
def rename_quiz(quiz_id):
    new_name = request.form.get('new_name')
    print("New Name:", new_name)
    # Update the quiz_name in the database
    quiz = Quiz.query.get(quiz_id)
    quiz.quiz_name = new_name
    db.session.commit()

    return redirect(url_for('main.dashboard'))



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
    if 'user_id' not in session:
        flash('You must be logged in to access the dashboard', 'warning')
        return redirect(url_for('main.login'))

    user_id = session['user_id']

    quizzes = Quiz.query.filter_by(user_id=user_id).order_by(Quiz.datetime.desc()).all()

    for quiz in quizzes:
        quiz.datetime = quiz.datetime.strftime('%B %d, %Y %H:%M')  # Format the date as desired

    # Sort the quizzes based on their public status (public quizzes first)
    quizzes.sort(key=lambda quiz: not quiz.public_quiz)

    return render_template('dashboard.html', quizzes=quizzes)



@main.route('/toggle_public', methods=['POST'])
def toggle_public():
    data = request.get_json()
    quiz_id = data.get('quizId')
    is_public = data.get('isPublic')

    # Update the public_quiz attribute for the quiz with the given ID
    quiz = Quiz.query.get(quiz_id)
    if quiz:
        quiz.public_quiz = is_public
        db.session.commit()

    return jsonify({'success': True})
