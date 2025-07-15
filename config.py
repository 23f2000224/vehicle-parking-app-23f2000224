class CONFIG():
    DEBUG = False
    SQLALCHEMY_TRACK_MODIFICATIONS = True

class LocalDevelopmentConfig(CONFIG):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///parking_lot.db.sqlite'
    SECRET_KEY = 'secret_key'