from flask import Flask
from flask_restful import Api
import logging

app = Flask(__name__)
app.logger.setLevel(logging.INFO)
api = Api(app)


@app.get("/hello")
def hello():
    return {"message": "Hello World from auth service"}, 200


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
