import os


class Config(object):
    DEBUG = True
    TESTING = False


class DevelopmentConfig(Config):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'
    OPENAI_KEY = os.environ.get('OPENAI_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///db.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    TOASTR_POSITION_CLASS = 'toast-bottom-right'


class TestingConfig(Config):
    SECRET_KEY = os.environ.get('SECRET_KEY')
    OPENAI_KEY = os.environ.get('OPENAI_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True


class ProductionConfig(Config):
    SECRET_KEY = os.environ.get('SECRET_KEY')
    OPENAI_KEY = os.environ.get('OPENAI_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    TOASTR_POSITION_CLASS = 'toast-bottom-right'


config = {
    'development': DevelopmentConfig(),
    'testing': TestingConfig(),
    'production': ProductionConfig()
}
