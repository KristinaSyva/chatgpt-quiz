import os
class Config(object):
    DEBUG = True
    TESTING = False

class DevelopmentConfig(Config):
    SECRET_KEY = os.environ.get('SECRET_KEY')
    OPENAI_KEY = os.environ.get('OPENAI_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
class TestingConfig(Config):
    SECRET_KEY = os.environ.get('SECRET_KEY')
    OPENAI_KEY = os.environ.get('OPENAI_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
class ProductionConfig(Config):
    SECRET_KEY = os.environ.get('SECRET_KEY')
    OPENAI_KEY = os.environ.get('OPENAI_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
config = {
    'development': DevelopmentConfig(),
    'testing': TestingConfig(),
    'production': ProductionConfig()
}
