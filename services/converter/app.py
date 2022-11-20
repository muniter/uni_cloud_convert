import json
from pathlib import Path
from pydub import AudioSegment
from email_service import send_notification
from database import db_session
from cloud import get_file, initialize_subscription, put_file

import logging

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("converter")


def manager(message):
    message_data = json.loads(message.data)
    logger.info(f"Got message: {message_data}")
    try:
        type, data = message_data["type"], message_data["data"]
        if type == "convert":
            convert(**data)
        elif type == "ping":
            ping(data)
        elif type == "db_health":
            db_health()
        else:
            logger.error(f"Unknown message type: {type}")

        return True
    except Exception as e:
        logger.error(f"Error processing message: {e}, with data: {message_data}")
        return False


def db_health():
    logger.info("Checking database health")
    db_session.execute("SELECT 1")
    logger.info("Database health is OK")
    return "OK"


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


def convert(file_id, uploaded_filename, new_format, email):
    logger.info(f"Converting {uploaded_filename} to {new_format}")

    # Download the file from the cloud to temp dir
    source = Path("/tmp", uploaded_filename)
    get_file(uploaded_filename, source)

    if not source.exists():
        # Retry the task in 5 seconds
        logger.error(f"File {uploaded_filename} not found, task will be retried")
        raise FileNotFoundError("File not found")

    destination = Path("/tmp", f"{file_id}.{new_format}")

    logger.info(f"Conversion of {uploaded_filename} to {new_format} started")
    # convert wav to mp3
    sound = AudioSegment.from_file(source)
    sound.export(destination)
    logger.info(f"Conversion of {uploaded_filename} to {new_format} finished")

    # Upload the file to the cloud
    put_file(destination)
    processed_size = destination.stat().st_size
    mark_conversion(file_id, destination.name, new_format, processed_size)

    # Cleanup the temp files
    source.unlink()
    destination.unlink()

    # ToDo if no es test
    send_notification(email, file_id)
    logger.info(f"Conversion for file_id: {file_id} completed")
    return True


if __name__ == "__main__":
    initialize_subscription(callback=manager)
