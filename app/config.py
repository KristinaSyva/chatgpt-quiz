import os

class Config(object):
    DEBUG = True
    TESTING = False

class DevelopmentConfig(Config):
    SECRET_KEY = os.environ.get('SECRET_KEY')
    OPENAI_KEY = os.environ.get('OPENAI_KEY')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    SQLALCHEMY_BINDS = {
        'primary': os.environ.get('DATABASE_URL')
    }

class TestingConfig(Config):
    SECRET_KEY = os.environ.get('SECRET_KEY')
    OPENAI_KEY = os.environ.get('OPENAI_KEY')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    SQLALCHEMY_BINDS = {
        'primary': os.environ.get('DATABASE_URL')
    }

class ProductionConfig(Config):
    SECRET_KEY = os.environ.get('SECRET_KEY')
    OPENAI_KEY = os.environ.get('OPENAI_KEY')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    SQLALCHEMY_BINDS = {
        'primary': os.environ.get('DATABASE_URL')
    }

config = {
    'development': DevelopmentConfig(),
    'testing': TestingConfig(),
    'production': ProductionConfig()
}
