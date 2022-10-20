import os
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
mnt_dir = '../../../mnt/'

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


@app.task(name="convert")
def make_conversion(original_filename, expected_format, receiver):
    without_extension = original_filename[0 : original_filename.rfind('.')]

    src = mnt_dir + original_filename
    dst = mnt_dir + without_extension + '.' + expected_format

    # convert wav to mp3                  
    logger.info("iniciando conversion")                 
    sound = AudioSegment.from_file(src)
    sound.export(dst)
    logger.info("finalizada conversion")                 
    
    #ToDo if no es test
    send_notification(original_filename, expected_format, receiver)
    #ToDo actualizar status en db

make_conversion("transcript.mp3", "wav", "asantamariap14@gmail.com")


