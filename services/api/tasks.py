import os
from pathlib import Path
import json
import uuid
from sqlalchemy import select, and_
from cloud import (
    delete_file,
    get_file,
    get_publish_client,
    put_file,
)
from database import db_session
from datetime import datetime
from app import app
from flask import request, send_file, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Task, User
from pydantic import BaseModel
from flask_pydantic import validate


class TaskUpdateBody(BaseModel):
    newFormat: str


def publish_task(task: Task, email):
    args = {
        "type": "convert",
        "data": {
            "file_id": task.file_id,
            "uploaded_filename": task.uploaded_filename,
            "new_format": task.new_format,
            "email": email,
        },
    }
    client, topic = get_publish_client()
    client.publish(topic, data=json.dumps(args).encode())


def task_serialize(task):
    return {
        "id": task.id,
        "timestamp": task.timestamp.isoformat() if task.timestamp else None,
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
        "uploaded_at": task.uploaded_at.isoformat() if task.uploaded_at else None,
        "processed_at": task.processed_at.isoformat() if task.processed_at else None,
    }


def data_serialize(row):
    return {"min": int(row.min), "count": int(row.count)}


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


@app.route("/benchmark/conversion/result", methods=["GET"])
def benchmark_conversion_result():
    tasks = db_session.execute(select([Task])).scalars().all()
    return [task_serialize(task) for task in tasks], 200


@app.route("/benchmark/conversion/data", methods=["GET"])
def benchmark_conversion_data():
    data = db_session.execute(
        """
        SELECT d.diff AS min,
               Count(d.id)
        FROM   (SELECT id,
                       Ceil(Extract(epoch FROM ( processed_at - uploaded_at )) / 60) AS
                       diff
                FROM   tasks
                WHERE  processed_at IS NOT NULL) AS d
        GROUP  BY d.diff
        ORDER  BY min
        """
    )
    response = jsonify([data_serialize(row) for row in data])
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


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


@app.route("/api/files/<string:file_id>", methods=["GET"])
@validate()
def get_converted_file(file_id: str):
    task = (
        db_session.execute(select([Task]).where(and_(Task.file_id == file_id)))
        .scalars()
        .one_or_none()
    )

    if task is None:
        return {"message": "File not found"}, 404

    if task.status != "processed":
        return {"message": "File not ready"}, 400

    file_path = Path("/tmp", task.processed_file)
    get_file(task.processed_file, file_path)
    return send_file(file_path, as_attachment=True)


def create_db_task(file, user_id, new_format, commit=True, filename=None) -> tuple[Task, User]:
    filename = filename or file.filename
    file_id = str(uuid.uuid4())
    file_extension = Path(filename).suffix.lstrip(".")
    file_upload_name = f"{file_id}.{file_extension}"
    file_upload_path = Path("/tmp", file_upload_name)

    # Save, pass path to gcp and then delete local
    with open(file_upload_path, "wb") as f:
        f.write(file.read())

    file_size = os.stat(file_upload_path).st_size
    if file_size == 0:
        raise Exception("File is empty")

    put_file(file_upload_path)
    os.remove(file_upload_path)

    new_task = Task(
        user_id=user_id,
        new_format=new_format,
        uploaded_filename=file_upload_name,
        file_id=file_id,
        original_file=filename,
        original_format=file_extension,
        original_size=file_size,
    )
    if commit:
        db_session.add(new_task)
        db_session.commit()

    user = (
        db_session.execute(select([User]).where(and_(User.id == user_id)))
        .scalars()
        .one_or_none()
    )

    user = db_session.execute(select([User]).where(User.id == user_id)).scalars().one()

    if user is None:
        raise Exception("User not found")

    return new_task, user


# Endpoint to create a new task
@app.route("/api/tasks", methods=["POST"])
@jwt_required()
def create_task():
    user_id = get_jwt_identity()["id"]
    user_email = (
        db_session.execute(select([User.email]).where(User.id == user_id))
        .scalars()
        .one_or_none()
    )

    if user_email is None:
        return {"message": "User not found"}, 404

    if "fileName" not in request.files:
        return {"message": "file not sent"}, 400

    file = request.files["fileName"]
    new_format = request.form["newFormat"].lower()

    if file.filename == "":
        return {"message": "file null"}, 400
    if not file:
        return {"message": "corrupted file"}, 400

    if new_format not in app.config["ALLOWED_FORMATS"]:
        return {"message": "newFormat value is not an allowed format"}, 400

    task, user = create_db_task(file, user_id, new_format)
    app.logger.info(
        """
        Task created: uploaded_file: %s, user_id: %s, original_format: %s, new_format: %s, \
        file_name: %s
        """,
        task.uploaded_filename,
        task.user_id,
        task.original_format,
        task.new_format,
        task.original_file,
    )
    publish_task(task, user.email)
    return {"message": "task created", "task": task_serialize(task)}, 200


# Endpoint to update a task, for changing the format
@app.route("/api/tasks/<int:task_id>", methods=["PUT"])
@jwt_required()
@validate()
def update_task(task_id: int, body: TaskUpdateBody):
    user_id = get_jwt_identity()["id"]
    new_format = body.newFormat.lower()

    if new_format not in app.config["ALLOWED_FORMATS"]:
        return {"message": "newFormat value is not an allowed format"}, 400

    user = (
        db_session.execute(select([User]).where(and_(User.id == user_id)))
        .scalars()
        .one_or_none()
    )

    task = (
        db_session.execute(select([Task]).where(Task.id == task_id))
        .scalars()
        .one_or_none()
    )

    if not task:
        return {"message": "task not found"}, 404

    if task.processed_file:
        app.logger.info("hay archivo procesado anteriormente")
        delete_file(task.processed_file)

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
    publish_task(task, user.email)

    return {"message": "task updated", "task": task_serialize(task)}, 200


@app.route("/benchmark/conversion/start", methods=["POST"])
def benchmark_conversion():
    user_id = 1
    user_email = (
        db_session.execute(select([User.email]).where(User.id == user_id))
        .scalars()
        .one_or_none()
    )
    tasks: list[Task] = []

    if user_email is None:
        return {"message": "User not found"}, 404

    if "fileName" not in request.files:
        return {"message": "file not sent"}, 400

    file = request.files["fileName"]
    new_format = request.form["newFormat"].lower()
    task_number = int(request.form["taskNumber"])

    if not file.filename:
        return {"message": "file null"}, 400
    if not file:
        return {"message": "corrupted file"}, 400

    if new_format not in app.config["ALLOWED_FORMATS"]:
        return {"message": "newFormat value is not an allowed format"}, 400

    if not task_number:
        return {"message": "taskNumber value is not an allowed format"}, 400

    response = Response(
        json.dumps({"message": f"Creating {task_number} tasks"}),
        status=200,
        content_type="application/json",
    )
    filename = file.name
    if filename is None:
        return {"message": "file name not found"}, 400

    file.save(Path("/tmp", filename))

    @response.call_on_close
    def generate_tasks():
        with open(Path("/tmp", filename), "rb") as file:
            for i in range(task_number):
                file.seek(0)
                app.logger.info(f"Creating task {i}")
                task, _ = create_db_task(file, user_id, new_format, commit=False, filename=filename)
                tasks.append(task)

            now = datetime.utcnow()
            for task in tasks:
                task.uploaded_at = now  # pyright: ignore

            db_session.add_all(tasks)
            db_session.commit()

            app.logger.info(f"Sending {task_number} task to conversion queue")
            for task in tasks:
                publish_task(task, user_email)
            app.logger.info(f"Tasks {task_number} sent to conversion queue")

    return response
