from pathlib import Path
from google.cloud.storage.bucket import NotFound
from google.cloud import storage
import os
from app import app

GCP_BUCKET_NAME = os.environ.get("GCP_BUCKET_NAME", None)
if GCP_BUCKET_NAME is None:
    raise ValueError("GCP_BUCKET_NAME is not set")

def get_bucket():
    client = storage.Client()
    return client.get_bucket(GCP_BUCKET_NAME)


def get_file(object_name: str, destination: Path):
    bucket = get_bucket()
    blob = bucket.blob(object_name)
    app.logger.info(f"Downloading {object_name} from GCP")
    blob.download_to_filename(destination)


def put_file(filename: Path):
    base = filename.name
    bucket = get_bucket()
    blob = bucket.blob(base)
    app.logger.info(f"Uploading file {base} to GCP")
    blob.upload_from_filename(filename)

def delete_file(filename: str):
    bucket = get_bucket()
    blob = bucket.blob(filename)
    app.logger.info(f"Deleting file {filename} from GCP")
    try:
        blob.delete()
    except NotFound:
        app.logger.info(f"File {filename} not found in GCP")
