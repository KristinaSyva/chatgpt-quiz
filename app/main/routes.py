from flask import Blueprint, render_template, request, redirect, url_for, \
    session, flash, jsonify
from datetime import datetime as dt
from sqlalchemy import func
from flask_login import current_user, login_required
from app.aiapi import generateChatResponse
from app.extensions import db
from app.models import GameQuestions, GameAnswers, Quiz, Scores

main = Blueprint('main', __name__)


@main.route('/dashboard')
@login_required
def dashboard():
    user_id = current_user.id

    user_quizzes = Quiz.query.filter_by(user_id=user_id).order_by(Quiz.datetime.desc()).all()
    public_quizzes = Quiz.query.filter(Quiz.public_quiz, Quiz.user_id != user_id).order_by(Quiz.datetime.desc()).all()

    for quiz in user_quizzes:
        quiz.datetime = quiz.datetime.strftime('%B %d, %Y %H:%M')  # Format the date as desired

    for quiz in public_quizzes:
        quiz.datetime = quiz.datetime.strftime('%B %d, %Y %H:%M')  # Format the date as desired

    return render_template('main/dashboard.html', user_quizzes=user_quizzes, public_quizzes=public_quizzes)


@main.route('/<int:user_id>/quiz/<int:quiz_id>', methods=['GET'])
@login_required
def quiz_page(user_id, quiz_id):
    print(user_id, quiz_id)
    quiz = Quiz.query.filter_by(user_id=user_id, id=quiz_id).first()
    print(quiz)
    if quiz is None:
        flash('Quiz not found', 'error')
        return redirect(url_for('main.dashboard'))

    questions = GameQuestions.query.filter_by(quiz_id=quiz.id).all()
    if not questions:
        flash('No questions found for the quiz', 'error')
        return redirect(url_for('main.dashboard'))

    answer_options = []
    for question in questions:
        options = GameAnswers.query.filter_by(question_id=question.id).all()
        answer_options.extend(options)

    return render_template('main/generated-quiz.html', quiz=quiz, questions=questions, answer_options=answer_options)


@main.route('/submit-quiz', methods=['POST'])
@login_required
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
        correct_count = sum \
            (1 for question_id, user_answer in user_answers.items() if user_answer == correct_answers.get(question_id))

        if total_questions > 0:
            score_percentage = (correct_count / total_questions) * 100
        else:
            score_percentage = 0

        # Check if the user has already taken the same quiz
        quiz_id = int(request.form.get('quiz_id'))
        user_id = current_user.id
        existing_score = Scores.query.filter_by(user_id=user_id, quiz_id=quiz_id).first()

        if existing_score:
            # Update the existing score
            existing_score.score_percentage = score_percentage
            existing_score.datetime = dt.now()
        else:
            # Create a new Scores record
            score = Scores(user_id=user_id, datetime=dt.now(), score_percentage=score_percentage, quiz_id=quiz_id)
            db.session.add(score)

        db.session.commit()

        # Return the score as JSON response
        return jsonify(score_percentage=score_percentage)

    except Exception as e:
        # Log the error with traceback
        import traceback
        traceback.print_exc()

        # Return an error response
        return jsonify({'error': 'Error processing quiz submission'}), 400


@main.route('/quiz/<int:quiz_id>/score', methods=['GET'])
@login_required
def scoreboard(quiz_id):
    users = Scores.query.order_by(Scores.score_percentage.desc()).filter_by(quiz_id=quiz_id).all()
    quiz = Quiz.query.filter_by(id=quiz_id).first()
    return render_template('main/scoreboard.html', users=users, quiz=quiz)


@main.route('/quiz', methods=['GET', 'POST'])
@login_required
def quiz_view():
    if request.method == 'POST':
        prompt = request.form['prompt']
        res = generateChatResponse(prompt)

        # Store the quiz data in the session

        # print("Generated Quiz Data:", res)
        if 'error' in res:
            session.pop('quiz_data', None)
            return jsonify(res), 400
        session['quiz_data'] = res
        return jsonify(res), 200

    return render_template('main/quiz.html')


@main.route('/generate-quiz', methods=['POST'])
@login_required
def generate_quiz():
    user_id = current_user.id

    current_datetime = dt.now()

    # Retrieve the quiz data from the request
    res = session.get('quiz_data', None)

    print("Generated Quiz Data:", res)

    if res is None:
        return jsonify({"error": "Quiz data not found in request"}), 400

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
    session.pop('quiz_data', None)
    return jsonify({"success": "Generate Quiz Successfully"}), 200


@main.route('/delete-quiz/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def delete_quiz(quiz_id):
    # Retrieve the quiz by ID
    quiz = Quiz.query.get(quiz_id)

    print(quiz)

    if not quiz:
        flash('Quiz not found', 'error')
        return redirect(url_for('main.dashboard'))

    # Check if the logged-in user is the owner of the quiz
    if quiz.user_id != current_user.id:
        flash('You are not authorized to delete this quiz', 'error')
        return redirect(url_for('main.dashboard'))

    # Delete the associated GameQuestions and GameAnswers records
    Scores.query.filter_by(user_id=current_user.id, quiz_id=quiz_id).delete()
    game_questions = GameQuestions.query.filter_by(quiz_id=quiz.id).all()
    for question in game_questions:
        GameAnswers.query.filter_by(question_id=question.id).delete()
    GameQuestions.query.filter_by(quiz_id=quiz.id).delete()

    db.session.delete(quiz)
    db.session.commit()

    flash('Quiz deleted successfully', 'success')
    return redirect(url_for('main.dashboard'))


@main.route('/rename_quiz/<int:quiz_id>', methods=['POST'])
@login_required
def rename_quiz(quiz_id):
    new_name = request.form.get('new_name')
    print("New Name:", new_name)
    # Update the quiz_name in the database
    quiz = Quiz.query.get(quiz_id)
    quiz.quiz_name = new_name
    db.session.commit()

    return redirect(url_for('main.dashboard'))


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
