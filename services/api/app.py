from database import db_session, init_db
from flask import Flask
from flask_restful import Api
import logging

# Set up the models, create the database tables
app = Flask(__name__)
app.logger.setLevel(logging.INFO)
app.config["JWT_SECRET_KEY"] = "secret-jwt"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = False
api = Api(app)


# Teardown the database session
@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


@app.before_first_request
def init():
    # remove the file and create a new one
    app.logger.info("Got the first request, initializing the database")
    init_db()
    app.logger.info("Database initialized")


@app.get("/")
def index():
    return {"message": "Hello World"}, 200


@app.get("/health")
def health():
    db_session.execute("SELECT 1")
    return {"datbase": "OK"}, 200


def create_app():
    return app
