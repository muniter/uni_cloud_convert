from ast import If
from email import header
from flask import Flask, request
from flask_restful import Api, Resource
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, JWTManager
import logging


app = Flask(__name__)
app.logger.setLevel(logging.INFO)
app.config["JWT_SECRET_KEY"] = "secret-jwt"  # Change this!
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = False
jwt = JWTManager(app)
api = Api(app)

users = [
    {
        "username": "admin",
        "password": "admin",
    },
    {
        "username": "user",
        "password": "user",
    },
]


@app.get("/hello")
def hello():
    return {"message": "Hello World from auth service"}, 200


class Signup(Resource):
    def post(self):
        data = request.get_json()
        username = data["username"]
        password = data["password"]
        if username in [user["username"] for user in users]:
            return {"message": "Username already exists"}, 400
        users.append({"username": username, "password": password})
        return {"message": "User created successfully"}, 201

    def get(self):
        return {"users": users}, 200


class Login(Resource):
    def post(self):
        data = request.get_json()
        username = data["username"]
        password = data["password"]
        for user in users:
            if user["username"] == username and user["password"] == password:
                access_token = create_access_token(identity=username)
                return {"access_token": access_token}, 200
        return {"message": "Invalid credentials"}, 401


api.add_resource(Signup, '/signup')
api.add_resource(Login, '/login')

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
