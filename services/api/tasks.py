import os
from sqlalchemy import select, and_
from database import db_session
from app import app
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Task
from flask_pydantic import validate


def task_serialize(task):
    return {
        "id": task.id,
        "status": task.status,
        "user_id": task.user_id,
        "original_file": task.original_file,
        "original_format": task.original_format,
        "original_size": task.original_size,
        "processed_file": task.processed_file,
        "processed_format": task.processed_format,
        "processed_size": task.processed_size,
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
    new_format = request.form['newFormat']
    if file.filename == '':
        return {"message": "file null"}, 400
    if not file:
        return {"message": "corrupted file"}, 400
        
    file_upload_name = "uploaded.{}".format(file.filename.rsplit('.', 1)[1].lower())
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], file_upload_name))
    app.logger.info("uploaded file {} as {} to convert to {}".format(file.filename, file_upload_name, new_format))
    return {"message": "uploaded file {} as {} to convert to {}".format(file.filename, file_upload_name, new_format)}, 200


# Endpoint to update a task, for changing the format
@app.route("/api/tasks/<int:task_id>", methods=["PUT"])
@jwt_required()
def update_task(task_id: int):
    user_id = get_jwt_identity()["id"]
    raise NotImplementedError
