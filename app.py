from flask import Flask
from models import db, populate
from flask_login import LoginManager
from config import LocalDevelopmentConfig

def create_app():
    app = Flask(__name__)
    app.config.from_object(LocalDevelopmentConfig)
    db.init_app(app)

    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)

    # User loader callback
    from models.models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    app.app_context().push()
    return app

app = create_app()

with app.app_context():
    from controllers import controllers, user_controllers, admin_controllers
    db.create_all()
    populate.populate_db()

if __name__ == '__main__':
    app.run(debug=True)