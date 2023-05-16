from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db
from datetime import datetime

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_name = db.Column(db.String(255), nullable=True)
    user_id = db.Column(db.Integer, nullable=False)
    datetime = db.Column(db.DateTime, nullable=False)
    quiz_number = db.Column(db.Integer, nullable=False)
    public_quiz = db.Column(db.Boolean, nullable=False, default=False)

    score_records = db.relationship('Scores', back_populates='quiz', lazy=True)

    scores = db.relationship(
        'Scores',
        back_populates='quiz_obj',
        lazy='dynamic',
        overlaps="quiz,score_records"
    )
class GameQuestions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    datetime = db.Column(db.DateTime, nullable=False)
    quiz_number = db.Column(db.Integer, nullable=False)
    question_number = db.Column(db.Integer, nullable=False)
    question_text = db.Column(db.String(1000), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)

    quiz = db.relationship('Quiz', backref=db.backref('questions', lazy=True))

class GameAnswers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    datetime = db.Column(db.DateTime, nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('game_questions.id'), nullable=False)
    answer_letter = db.Column(db.String(1), nullable=False)
    answer_text = db.Column(db.String(1000), nullable=False)
    correct_answer = db.Column(db.Boolean, nullable=False)

    quiz = db.relationship('Quiz', backref=db.backref('answers', lazy=True))
    question = db.relationship('GameQuestions', backref=db.backref('answers', lazy=True))   
    
class Scores(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    datetime = db.Column(db.DateTime, nullable=False)
    score_percentage = db.Column(db.Float, nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)

    user = db.relationship('User', backref=db.backref('scores', lazy=True))
    quiz = db.relationship('Quiz', back_populates='score_records')
    quiz_obj = db.relationship('Quiz', back_populates='scores', overlaps="quiz,score_records")
    
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)  # Add username field
    password_hash = db.Column(db.String(128))
    email = db.Column(db.String(120), unique=True, nullable=False)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

