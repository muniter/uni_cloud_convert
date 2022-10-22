import os
import pathlib
from pydub import AudioSegment
from celery import Celery
from email_service import send_notification
from database import db_session

import logging

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("converter")
mnt_dir = "/mnt"
# Setup dst_dir
dst_dir = pathlib.Path(mnt_dir) / "converted_files"
if not dst_dir.exists():
    dst_dir.mkdir()

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


@app.task(name="convert")
def make_conversion(file_id, filename, expected_format, email):
    logger.info(f"Converting {filename} to {expected_format}")
    without_extension = pathlib.Path(filename).stem

    src = pathlib.Path(mnt_dir) / "uploaded_files" / filename
    processed_name = f"{without_extension}.{expected_format}"
    dst = dst_dir / processed_name

    # convert wav to mp3
    sound = AudioSegment.from_file(src)
    sound.export(dst)
    processed_size = dst.stat().st_size
    mark_conversion(file_id, processed_name, expected_format, processed_size)
    # ToDo if no es test
    send_notification(email, file_id)
    logger.info(f"Conversion for file_id: {file_id} completed")
    return True
