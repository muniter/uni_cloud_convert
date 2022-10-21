import re
from flask import request
from sqlalchemy import select, or_
from flask_jwt_extended import create_access_token, JWTManager
from database import db_session
from app import app
from models import User
from pydantic import BaseModel
from flask_pydantic import validate

PASSWORD_MIN_LEN = 5
PASSWORD_MAX_LEN = 20
PASSWORD_REQUIRED_SPECIAL_CHARS = "[$#@]"

jwt = JWTManager(app)


class UserRegistationBody(BaseModel):
    username: str
    password1: str
    password2: str
    email: str


class LoginBody(BaseModel):
    username: str
    password: str


def user_exists(username, email):
    query = select(User).where(or_(User.username == username, User.email == email))
    return db_session.execute(query).first() is not None


def valid_password(password):
    valid = False
    while not valid:  
        if (len(password)<PASSWORD_MIN_LEN or len(password)>PASSWORD_MAX_LEN):
            break
        elif not re.search("[a-z]",password):
            break
        elif not re.search("[0-9]",password):
            break
        elif not re.search("[A-Z]",password):
            break
        elif not re.search(PASSWORD_REQUIRED_SPECIAL_CHARS,password):
            break
        elif re.search("\s",password):
            break
        else:
            valid=True
            break
    return valid


def create_user(username, email, password):
    user = User(username=username, email=email, password=password)
    db_session.add(user)
    db_session.commit()
    return user


def access_token(id, username):
    return create_access_token(identity={"id": id, "username": username})


@app.route("/api/auth/signup", methods=["POST"])
@validate()
def signup(body: UserRegistationBody):
    if user_exists(body.username, body.email):
        return {"message": "Username or email already exists"}, 400
    if body.password1 != body.password2:
        return {"message": "Passwords don't match"}, 400
    if not valid_password(body.password1) :
        message = "Password does not meet the minimum security conditions. "\
                  "It must have between {} and {} characters, at least one lowercase, "\
                  "one uppercase, one number, one character {} and no whitespace"\
                  .format(PASSWORD_MIN_LEN, PASSWORD_MAX_LEN, PASSWORD_REQUIRED_SPECIAL_CHARS)
        return {"message": message}, 400
    else:
        user = create_user(
            username=body.username,
            email=body.email,
            password=body.password1,
        )
        return {
            "message": "User created successfully",
            "access_token": access_token(user.id, user.username),
        }, 201


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
        return {"access_token": access_token(user.id, user.username)}, 200

    return {"message": "Invalid credentials"}, 401
