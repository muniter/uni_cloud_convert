from pathlib import Path
from google.cloud.storage.bucket import NotFound
from google.cloud import storage
import os
import logging

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("converter")


GCP_BUCKET_NAME = os.environ.get("GCP_BUCKET_NAME", None)
if GCP_BUCKET_NAME is None:
    raise ValueError("GCP_BUCKET_NAME is not set")


def get_bucket():
    client = storage.Client()
    return client.get_bucket(GCP_BUCKET_NAME)


def get_file(object_name: str, destination: Path):
    bucket = get_bucket()
    logger.info(f"Downloading file: {object_name} from GCP")
    blob = bucket.blob(object_name)
    blob.download_to_filename(destination)


def put_file(filename: Path):
    base = filename.name
    bucket = get_bucket()
    blob = bucket.blob(base)
    logger.info(f"Uploading file: {base} to GCP")
    blob.upload_from_filename(filename)
