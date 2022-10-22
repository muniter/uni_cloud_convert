import os
from pydub import AudioSegment
from celery import Celery
from email_service import send_notification
from database import db_session
from datetime import datetime
from sqlalchemy import select
from models import Task

import logging

UPLOAD_FOLDER = '/mnt/uploaded_files'
CONVERT_FOLDER = '/mnt/converted_files'

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


@app.task(name="convert")
def make_conversion(task_id, original_filename, expected_format, receiver):
    isExist = os.path.exists(CONVERT_FOLDER)
    if not isExist:
      os.makedirs(CONVERT_FOLDER)
    
    without_extension = original_filename[0 : original_filename.rfind('.')]
    convert_filename = without_extension + '.' + expected_format

    src = os.path.join(UPLOAD_FOLDER, original_filename)
    dst = os.path.join(CONVERT_FOLDER, convert_filename)
    
    # convert wav to mp3                  
    logger.info("iniciando conversion")                 
    sound = AudioSegment.from_file(src)
    sound.export(dst)
    logger.info("finalizada conversion")     
    file_size = os.stat(dst).st_size            
    
    task = (
        db_session.execute(
            select([Task]).where(Task.id == task_id)
        )
        .scalars()
        .one_or_none()
    )
    
    task.status = "processed"
    task.processed_file = convert_filename 
    task.processed_format = expected_format 
    task.processed_size = file_size 
    task.processed_at = datetime.utcnow() 
    db_session.commit()
    logger.info("conversión actualizada en bd")
    
    send_notification(original_filename, expected_format, receiver)

#make_conversion("transcript.mp3", "wav", "asantamariap14@gmail.com")


