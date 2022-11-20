from pathlib import Path
from typing import Callable
from google.api_core.exceptions import AlreadyExists
from google.cloud.storage.bucket import NotFound
from google.cloud import storage, pubsub_v1
import os
import logging

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("converter")


GCP_BUCKET_NAME = os.environ.get("GCP_BUCKET_NAME", None)
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID", None)
GCP_CONVERTER_SUBSCRIPTION = os.environ.get("GCP_CONVERTER_SUBSCRIPTION", None)
GCP_CONVERTER_TOPIC = os.environ.get("GCP_CONVERTER_TOPIC", None)

# Validation
if GCP_BUCKET_NAME is None:
    raise ValueError("GCP_BUCKET_NAME is not set")
if GCP_PROJECT_ID is None:
    raise ValueError("GCP_PROJECT_ID is not set")
if GCP_CONVERTER_SUBSCRIPTION is None:
    raise ValueError("GCP_CONVERTER_SUBSCRIPTION is not set")
if GCP_CONVERTER_SUBSCRIPTION is None:
    raise ValueError("GCP_CONVERTER_SUBSCRIPTION is not set")


def get_bucket():
    client = storage.Client()
    return client.get_bucket(GCP_BUCKET_NAME)


def get_file(object_name: str, destination: Path):
    bucket = get_bucket()
    logger.info(f"Downloading file: {object_name} from GCP")
    blob = bucket.blob(object_name)
    blob.download_to_filename(destination)
    logger.info(f"Downloaded file: {object_name} from GCP")


def put_file(filename: Path):
    base = filename.name
    bucket = get_bucket()
    blob = bucket.blob(base)
    logger.info(f"Uploading file: {base} to GCP")
    blob.upload_from_filename(filename)
    logger.info(f"Uploaded file: {base} to GCP")


def initialize_subscription(callback=Callable):
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = GCP_CONVERTER_SUBSCRIPTION
    with subscriber:
        try:
            logger.info(f"Creating subscription: {subscription_path}")
            subscriber.create_subscription(
                request={"name": subscription_path, "topic": GCP_CONVERTER_TOPIC}
            )
            logger.info(f"Created subscription: {subscription_path}")
        except AlreadyExists:
            logger.info(f"Subscription already exists: {subscription_path}")

        future = subscriber.subscribe(subscription_path, callback=callback)
        logger.info(f"Subscribed to {subscription_path}")
        try:
            future.result()
            # Stop on keybard interrupt, and signals
        except KeyboardInterrupt:
            future.cancel()
            logger.info("Received keyboard interrupt, stopping")
