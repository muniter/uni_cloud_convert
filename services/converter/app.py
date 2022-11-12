import os
from pathlib import Path
from pydub import AudioSegment
from celery import Celery
from email_service import send_notification
from database import db_session
from cloud import get_file, put_file

import logging

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("converter")

# RabbitMQ connection, read from the environment
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL")
if not CELERY_BROKER_URL:
    raise ValueError("Missing CELERY_BROKER_URL environment variable")


app = Celery("cloud_convert", broker=CELERY_BROKER_URL)


@app.task(name="db_health")
def db_health():
    logger.info("Checking database health")
    db_session.execute("SELECT 1")
    logger.info("Database health is OK")
    return "OK"


@app.task(name="ping")
def ping(payload):
    logger.info(f"Got ping: {payload}, here is your pong")
    return True


def mark_conversion(file_id, processed_file, processed_format, processed_size):
    db_session.execute(
        """
       UPDATE tasks
       SET
           status = 'processed',
           processed_at = NOW(),
           processed_file = :processed_file,
           processed_format = :processed_format,
           processed_size = :processed_size
       WHERE file_id = :file_id
       """,
        {
            "file_id": file_id,
            "processed_file": processed_file,
            "processed_format": processed_format,
            "processed_size": processed_size,
        },
    )
    db_session.commit()


@app.task(name="convert", bind=True)
def make_conversion(self, file_id, filename, expected_format, email):
    logger.info(f"Converting {filename} to {expected_format}")

    # Download the file from the cloud to temp dir
    source = Path("/tmp", filename)
    get_file(filename, source)

    if not source.exists():
        # Retry the task in 5 seconds
        logger.error(f"File {filename} not found, task will be retried")
        return self.retry(
            countdown=5, max_retries=5, exc=FileNotFoundError(f"{filename} not found")
        )

    destination = Path("/tmp", Path(Path(filename).stem + f".{expected_format}"))

    logger.info(f"Conversion of {filename} to {expected_format} started")
    # convert wav to mp3
    sound = AudioSegment.from_file(source)
    sound.export(destination)
    logger.info(f"Conversion of {filename} to {expected_format} finished")

    # Upload the file to the cloud
    put_file(destination)
    processed_size = destination.stat().st_size
    mark_conversion(file_id, destination.name, expected_format, processed_size)

    # Cleanup the temp files
    source.unlink()
    destination.unlink()

    # ToDo if no es test
    send_notification(email, file_id)
    logger.info(f"Conversion for file_id: {file_id} completed")
    return True
