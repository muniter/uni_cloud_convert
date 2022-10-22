import os
from sqlalchemy import select, and_
from database import db_session
from datetime import datetime
from app import app
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Task, User
from flask_pydantic import validate
from werkzeug.utils import secure_filename
from celery import Celery

NEW_FORMAT_VALID = {"mp3", "acc", "ogg", "wav", "wma"}
CONVERT_FOLDER = '/mnt/converted_files'

def make_celery(app):

    celery = Celery("cloud_convert")
    celery.conf.update(app.config["CELERY_CONFIG"])

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

celery = make_celery(app)

def task_serialize(task):
    return {
        "id": task.id,
        "timestamp": task.timestamp,
        "status": task.status,
        "user_id": task.user_id,
        "new_format": task.new_format,
        "uploaded_filename": task.uploaded_filename,
        "original_file": task.original_file,
        "original_format": task.original_format,
        "original_size": task.original_size,
        "processed_file": task.processed_file,
        "processed_format": task.processed_format,
        "processed_size": task.processed_size,
        "uploaded_at": task.uploaded_at,
        "processed_at": task.processed_at,
    }


@app.route("/api/tasks", methods=["GET"])
@jwt_required()
def get_tasks():
    user_id = get_jwt_identity()["id"]
    tasks = (
        db_session.execute(select([Task]).where(Task.user_id == user_id))
        .scalars()
        .all()
    )
    return [task_serialize(task) for task in tasks], 200


@app.route("/api/tasks/<int:task_id>", methods=["GET"])
@jwt_required()
@validate()
def get_task(task_id: int):
    user_id = get_jwt_identity()["id"]
    task = (
        db_session.execute(
            select([Task]).where(and_(Task.id == task_id, Task.user_id == user_id))
        )
        .scalars()
        .one_or_none()
    )
    if task is None:
        return {"message": "Task not found"}, 404

    return task_serialize(task), 200


@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
@jwt_required()
@validate()
def delete_task(task_id: int):
    user_id = get_jwt_identity()["id"]
    task = (
        db_session.execute(
            select([Task]).where(and_(Task.id == task_id, Task.user_id == user_id))
        )
        .scalars()
        .one_or_none()
    )
    if task is None:
        return {"message": "Task not found"}, 404

    db_session.delete(task)
    db_session.commit()
    return {"message": "Task deleted successfully"}, 200


@app.route("/api/files/<int:task_id>", methods=["GET"])
@jwt_required()
@validate()
def get_file(task_id: str):
    user_id = get_jwt_identity()["id"]
    task = (
        db_session.execute(
            select([Task]).where(and_(Task.id == task_id, Task.user_id == user_id))
        )
        .scalars()
        .one_or_none()
    )

    # TODO: retrieve file and send it back
    filename = task.processed_file
    raise NotImplementedError


# Endpoint to create a new task
@app.route("/api/tasks", methods=["POST"])
@jwt_required()
def create_task():
    user_id = get_jwt_identity()["id"]
    if 'fileName' not in request.files:
        return {"message": "file not sent"}, 400
    
    file = request.files['fileName']
    new_format = request.form['newFormat'].lower()
    
    if file.filename == '':
        return {"message": "file null"}, 400
    if not file:
        return {"message": "corrupted file"}, 400
        
    file_extension = file.filename.rsplit('.', 1)[1].lower()
    file_upload_name = secure_filename(file.filename)
    file_upload_path = os.path.join(app.config['UPLOAD_FOLDER'], file_upload_name)
    
    if os.path.exists(file_upload_path):
        return {"message": "file exits"}, 403
      
    if new_format is None or not new_format or new_format not in NEW_FORMAT_VALID:
      return {"message": "newFormat value not valid in {}".format(NEW_FORMAT_VALID)}, 400
    
    file.save(file_upload_path)
    file_size = os.stat(file_upload_path).st_size
        
    new_task = Task(user_id=user_id,\
                    new_format=new_format,\
                    uploaded_filename=file_upload_name,\
                    original_file=file.filename,\
                    original_format=file_extension,\
                    original_size=file_size)
    db_session.add(new_task)
    db_session.commit()
    
    user = (
        db_session.execute(
            select([User]).where(and_(User.id == user_id))
        )
        .scalars()
        .one_or_none()
    ) 
    
    task = (
        db_session.execute(
            select([Task]).where(and_(Task.id == new_task.id, Task.user_id == user_id))
        )
        .scalars()
        .one_or_none()
    ) 
    
    app.logger.info("Sending task to convert")
    celery.send_task("convert", args=[task.id, file_upload_name, new_format, user.email])
    
    message = "uploaded file '{}' as '{}' to convert to '{}'".format(file.filename, file_upload_name, new_format)
    app.logger.info(message)
    return {"message": message, "task": task_serialize(task)}, 200


# Endpoint to update a task, for changing the format
@app.route("/api/tasks/<int:task_id>", methods=["PUT"])
@jwt_required()
def update_task(task_id: int):
    user_id = get_jwt_identity()["id"]
    new_format = request.json.get("newFormat", None).lower()
    
    user = (
        db_session.execute(
            select([User]).where(and_(User.id == user_id))
        )
        .scalars()
        .one_or_none()
    ) 
    
    task = (
        db_session.execute(
            select([Task]).where(Task.id == task_id)
        )
        .scalars()
        .one_or_none()
    )
    
    if not task:
      return {"message": "task not found"}, 404
    
    if new_format is None or not new_format or new_format not in NEW_FORMAT_VALID:
      return {"message": "newFormat value not valid in {}".format(NEW_FORMAT_VALID)}, 400
        
    if task.processed_file:
      app.logger.info("hay archivo procesado anteriormente")
      prev = os.path.join(CONVERT_FOLDER, task.processed_file)
      if os.path.exists(prev):
        app.logger.info("si existe, eliminar")
        os.remove(prev)
        
    task.timestamp = datetime.utcnow() 
    task.status = "uploaded"
    task.user_id = user_id 
    task.new_format = new_format 
    task.processed_file = None 
    task.processed_format = None 
    task.processed_size = None 
    task.processed_at = None 
    
    db_session.commit()
    
    app.logger.info("Sending task to convert")
    celery.send_task("convert", args=[task.id, task.uploaded_filename, new_format, user.email])
    
    return {"message": "task updated", "task": task_serialize(task)}, 200
