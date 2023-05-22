from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db, login_manager
from flask_login import UserMixin


class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_name = db.Column(db.String(255), nullable=True)
    user_id = db.Column(db.Integer, nullable=False)
    datetime = db.Column(db.DateTime, nullable=False)
    quiz_number = db.Column(db.Integer, nullable=False)
    public_quiz = db.Column(db.Boolean, nullable=False, default=False)


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
    quiz = db.relationship('Quiz', backref=db.backref('scores', lazy=True))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))
