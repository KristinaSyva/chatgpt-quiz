from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime as dt
from sqlalchemy import func
from datetime import datetime
import re


from .aiapi import generateChatResponse
from .extensions import db
from .models import User, GameQuestions, GameAnswers, Quiz, Scores

main = Blueprint('main', __name__)



@main.route('/user-<int:user_id>-quiz-<int:quiz_number>', methods=['GET'])
def quiz_page(user_id, quiz_number):
    try:
        quiz = Quiz.query.filter_by(user_id=user_id, quiz_number=quiz_number).first()
        if quiz is None:
            return "Quiz not found", 404

        if quiz.public_quiz or ('user_id' in session and session['user_id'] == user_id):
            questions = GameQuestions.query.filter_by(quiz_id=quiz.id).all()
            if not questions:
                return "No questions found for the quiz", 404

            answer_options = []
            for question in questions:
                options = GameAnswers.query.filter_by(question_id=question.id).all()
                answer_options.extend(options)

            user_scores = Scores.query.filter_by(user_id=session.get('user_id'), quiz_id=quiz.id).all()
            existing_scores_count = len(user_scores)

            return render_template('generated-quiz.html', quiz=quiz, questions=questions, answer_options=answer_options, existing_scores_count=existing_scores_count)

        return "Unauthorized", 401

    except Exception as e:
        # Log the error with traceback
        import traceback
        traceback.print_exc()
        flash('Error loading the quiz.', 'error')
        return redirect(url_for('main.dashboard'))


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

    # Clear the quiz data from the session
    session.pop('quiz_data', None)

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


@main.route('/submit-quiz', methods=['POST'])
def submit_quiz():
    try:
        user_answers = {}
        for key, value in request.form.items():
            if key.startswith('answer_'):
                question_id = int(key.split('_')[1])
                user_answers[question_id] = value

        # Fetch correct answers from the database based on the question IDs
        correct_answers = {}
        for question_id in user_answers.keys():
            question = GameQuestions.query.get(question_id)
            if question is not None:
                correct_answer = GameAnswers.query.filter_by(question_id=question.id, correct_answer=True).first()
                if correct_answer is not None:
                    correct_answers[question_id] = correct_answer.answer_letter

        # Calculate the score
        total_questions = len(correct_answers)
        correct_count = sum(1 for question_id, user_answer in user_answers.items() if user_answer == correct_answers.get(question_id))

        if total_questions > 0:
            score_percentage = round((correct_count / total_questions) * 100)
        else:
            score_percentage = 0

        # Check if the user has already taken the same quiz
        quiz_id = int(request.form.get('quiz_id'))
        user_id = session.get('user_id')

        # Check the number of existing scores for the same user and quiz
        existing_scores_count = Scores.query.filter_by(user_id=user_id, quiz_id=quiz_id).count()

        if existing_scores_count < 3:
            # Create a new Scores record
            score = Scores(user_id=user_id, datetime=dt.now(), score_percentage=score_percentage, quiz_id=quiz_id)
            db.session.add(score)
        else:
            # User has already reached the maximum number of attempts
            return "You have reached the maximum number of quiz attempts.", 400

        db.session.commit()

        # Return the score as JSON response
        return jsonify(score_percentage=score_percentage)

    except Exception as e:
        # Log the error with traceback
        import traceback
        traceback.print_exc()

        # Return an error response
        return "Error processing quiz submission", 400



@main.route('/user-<int:creator_id>-quiz-<int:quiz_number>/score', methods=['GET'])
def scoreboard(creator_id, quiz_number):
    quiz = Quiz.query.filter_by(user_id=creator_id, quiz_number=quiz_number).first()
    scores = Scores.query.filter_by(quiz_id=quiz.id).all()

    # Find the highest score for each user
    user_scores = {}
    for score in scores:
        if score.user.username in user_scores:
            if score.score_percentage > user_scores[score.user.username]:
                user_scores[score.user.username] = score.score_percentage
        else:
            user_scores[score.user.username] = score.score_percentage

    # Convert user_scores dictionary to a list of tuples for rendering in the template
    user_scores_list = [(username, round(score)) for username, score in user_scores.items()]

    return render_template('scoreboard.html', user_scores=user_scores_list, quiz=quiz)


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

'''
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

        # Password validation
        if len(password) < 8:
            flash('Password must be at least 8 characters long', 'danger')
            return redirect(url_for('main.register'))
        if not re.search(r'\d', password):
            flash('Password must contain at least one digit', 'danger')
            return redirect(url_for('main.register'))
        if not re.search(r'[A-Z]', password):
            flash('Password must contain at least one uppercase letter', 'danger')
            return redirect(url_for('main.register'))
        if not re.search(r'[a-z]', password):
            flash('Password must contain at least one lowercase letter', 'danger')
            return redirect(url_for('main.register'))
        if not re.search(r'[^a-zA-Z0-9]', password):
            flash('Password must contain at least one symbol', 'danger')
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

'''

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
    user = User.query.get(user_id)  # Retrieve the User object from the database

    user_quizzes = Quiz.query.filter_by(user_id=user_id).order_by(Quiz.datetime.desc()).all()
    public_quizzes = Quiz.query.filter(Quiz.public_quiz, Quiz.user_id != user_id).order_by(Quiz.datetime.desc()).all()

    for quiz in user_quizzes:
        quiz.datetime = quiz.datetime.strftime('%B %d, %Y %H:%M')  # Format the date as desired

    for quiz in public_quizzes:
        quiz.datetime = quiz.datetime.strftime('%B %d, %Y %H:%M')  # Format the date as desired

    return render_template('dashboard.html', user=user, user_quizzes=user_quizzes, public_quizzes=public_quizzes)




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
