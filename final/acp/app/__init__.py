from flask import Flask

def create_app():
    """
    Flask application factory. Registers blueprints and returns the app instance.
    """
    app = Flask(__name__)
    # Register the main blueprint
    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)
    return app
