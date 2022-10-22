from database import db_session, init_db
from flask import Flask, request, jsonify
import logging
import uuid
import os
import requests
from celery import Celery

# Set up the models, create the database tables
app = Flask(__name__)
app.logger.setLevel(logging.INFO)
app.config["JWT_SECRET_KEY"] = "secret-jwt"  # Change this!
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = False
app.config["UPLOAD_FOLDER"] = "/mnt/uploaded_files"
app.config["CONVERTED_FOLDER"] = "/mnt/converted_files"
app.config["ALLOWED_FORMATS"] = {"mp3", "acc", "ogg", "wav", "wma"}
app.config.update(CELERY_CONFIG={"broker_url": os.environ.get("CELERY_BROKER_URL")})

# Setup auth routes


def make_celery(app):

    celery = Celery("cloud_convert")
    celery.conf.update(app.config["CELERY_CONFIG"])

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


celery = make_celery(app)

# Teardown the database session
@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


@app.before_first_request
def init():
    # Set up the upload folder
    UPLOAD_FOLDER = app.config["UPLOAD_FOLDER"]
    if not os.path.exists(UPLOAD_FOLDER):
        os.mkdir(UPLOAD_FOLDER)

    app.logger.info("Got the first request, initializing the database")
    init_db()
    app.logger.info("Database initialized")


@app.get("/")
def index():
    return {"message": "Hello World"}, 200


@app.get("/ping")
def send():
    id = str(uuid.uuid4())
    payload = {"id": id, "mesage": "PING"}
    app.logger.info("Sending a task with payload %s", id)
    celery.send_task("ping", args=[payload])
    return {"message": "ping sent, check logs on converter for pong", "id": id}, 200


@app.get("/api-health")
def health():
    db_session.execute("SELECT 1")
    return {"database": "OK"}, 200


@app.get("/converter-health")
def convert_health():
    celery.send_task("db_health")
    return {
        "message": "Sent a task to check the database health, check converter logs"
    }, 200


def create_app():
    import auth
    import tasks

    return app
