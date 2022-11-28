from database import db_session, init_db
from flask import Flask
import logging
import uuid
import json

# Set up the models, create the database tables
app = Flask(__name__)
app.logger.setLevel(logging.INFO)
app.config["JWT_SECRET_KEY"] = "secret-jwt"  # Change this!
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = False
app.config["ALLOWED_FORMATS"] = {"mp3", "acc", "ogg", "wav", "wma"}

# Setup auth routes


# Teardown the database session
@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


@app.before_first_request
def init():
    from cloud import initialize_bucket, initialize_topic

    app.logger.info("Got the first request, initializing the pub/sub topic")
    initialize_topic()
    app.logger.info("Topic initialized")

    app.logger.info("Got the first request, initializing the bucket")
    initialize_bucket()
    app.logger.info("bucket initialized")

    app.logger.info("Got the first request, checking if the database is initialized")
    # Check if the table tasks exists, if not, initialize the database
    try:
        db_session.execute("SELECT 1 FROM tasks LIMIT 1")
        app.logger.info("Database is already initialized")
    except Exception:
        db_session.rollback()
        app.logger.info("Database not initialized, initializing")
        init_db()
        app.logger.info("Database initialized")


def get_pub_client():
    from cloud import get_publish_client

    return get_publish_client()


@app.get("/")
def index():
    return {"message": "Hello World"}, 200


@app.get("/ping")
def send():
    id = str(uuid.uuid4())
    payload = {"id": id, "message": "PING"}
    app.logger.info("Sending a task with payload %s", id)
    client, topic = get_pub_client()
    client.publish(topic, data=json.dumps({"type": "ping", "data": payload}).encode())
    return {"message": "ping sent, check logs on converter for pong", "id": id}, 200


@app.get("/api-health")
def health():
    db_session.execute("SELECT 1")
    return {"database": "OK"}, 200


@app.get("/alive")
def alive():
    return {"message": "I'm alive!"}


@app.get("/converter-health")
def convert_health():
    client, topic = get_pub_client()
    client.publish(topic, data=json.dumps({"type": "db_health", "data": {}}).encode())
    return {
        "message": "Sent a task to check the database health, check converter logs"
    }, 200


def create_app():
    import auth
    import tasks

    return app
