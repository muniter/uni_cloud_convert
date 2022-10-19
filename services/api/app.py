from urllib import response
from database import db_session, init_db
from flask import Flask, request, jsonify
from flask_restful import Api
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
app.config.update(
    CELERY_CONFIG={"broker_url": os.environ.get("CELERY_BROKER_URL")})

# Setup auth routes
import auth


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
    return app
