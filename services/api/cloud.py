from pathlib import Path
from google.api_core.exceptions import AlreadyExists
from google.cloud.storage.bucket import NotFound
from google.cloud import storage, pubsub_v1
import os
from app import app

GCP_BUCKET_NAME = os.environ.get("GCP_BUCKET_NAME", None)
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID", None)
GCP_CONVERTER_TOPIC = os.environ.get("GCP_CONVERTER_TOPIC", None)

# Validation
if GCP_BUCKET_NAME is None:
    raise ValueError("GCP_BUCKET_NAME is not set")
if GCP_PROJECT_ID is None:
    raise ValueError("GCP_PROJECT_ID is not set")
if GCP_CONVERTER_TOPIC is None:
    raise ValueError("GCP_CONVERTER_TOPIC is not set")


def initialize_bucket():
    try:
        get_bucket()
    except NotFound:
        app.logger.info(f"Initializing bucket {GCP_BUCKET_NAME}")
        storage.Client().create_bucket(GCP_BUCKET_NAME)


def get_bucket():
    client = storage.Client()
    return client.get_bucket(GCP_BUCKET_NAME)


def get_file(object_name: str, destination: Path):
    bucket = get_bucket()
    blob = bucket.blob(object_name)
    app.logger.info(f"Downloading {object_name} from GCP")
    blob.download_to_filename(destination)
    app.logger.info(f"Downloaded {object_name} from GCP")


def put_file(filename: Path):
    base = filename.name
    bucket = get_bucket()
    blob = bucket.blob(base)
    app.logger.info(f"Uploading file {base} to GCP")
    blob.upload_from_filename(filename)
    app.logger.info(f"Uploaded file {base} to GCP")


def delete_file(filename: str):
    bucket = get_bucket()
    blob = bucket.blob(filename)
    app.logger.info(f"Deleting file {filename} from GCP")
    try:
        blob.delete()
    except NotFound:
        app.logger.info(f"File {filename} not found in GCP")
    app.logger.info(f"Deleted file {filename} from GCP")


def initialize_topic():
    client, topic = get_publish_client()
    try:
        client.create_topic(name=topic)
    except AlreadyExists as e:
        app.logger.info(f"Topic {topic} already exists")
    except Exception as e:
        app.logger.info(
            f"Failed to create topic {GCP_CONVERTER_TOPIC}, aborting. Exception: {e}"
        )
        exit(1)


def get_publish_client():
    return pubsub_v1.PublisherClient(), GCP_CONVERTER_TOPIC
