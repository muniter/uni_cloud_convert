from flask import request
from sqlalchemy import select
from flask_jwt_extended import create_access_token, JWTManager
from database import db_session
from app import app
from models import User
from pydantic import BaseModel
from flask_pydantic import validate

jwt = JWTManager(app)


class UserRegistationBody(BaseModel):
    username: str
    password1: str
    password2: str
    email: str


class LoginBody(BaseModel):
    username: str
    password: str


def user_exists(username):
    query = select(User).where(User.username == username)
    return db_session.execute(query).one_or_none() is not None


def create_user(username, email, password):
    user = User(username=username, email=email, password=password)
    db_session.add(user)
    db_session.commit()


@app.route("/api/auth/signup", methods=["POST"])
@validate()
def signup(body: UserRegistationBody):
    # If passwords don't match return error
    if body.password1 != body.password2:
        return {"message": "Passwords don't match"}, 400
    if user_exists(body.username):
        return {"message": "Username already exists"}, 400
    else:
        create_user(
            username=body.username,
            email=body.email,
            password=body.password1,
        )
        return {"message": "User created successfully"}, 201


@app.route("/api/users", methods=["GET"])
def get_users():
    query = select(User)
    users = db_session.execute(query).scalars().all()
    app.logger.info("Got users from the database" + str(users))

    def serialize(user):
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "password": user.password,
        }

    return [serialize(user) for user in users]


@app.route("/api/auth/login", methods=["POST"])
@validate()
def login(body: LoginBody):
    user = db_session.query(User).filter_by(username=body.username).first()
    if user and user.password == body.password:
        token = create_access_token(identity={"id": user.id, "username": body.username})
        return {"access_token": token}, 200

    return {"message": "Invalid credentials"}, 401
