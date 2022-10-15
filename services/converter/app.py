import pika
import os

import logging

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("converter")

# RabbitMQ connection, read from the environment
RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST")
RABBITMQ_USER = os.environ.get("RABBITMQ_DEFAULT_USER")
RABBITMQ_PASS = os.environ.get("RABBITMQ_DEFAULT_PASS")

# Error if the environment variables are not set
if not all([RABBITMQ_HOST, RABBITMQ_USER, RABBITMQ_PASS]):
    logger.error("RabbitMQ environment variables are not set")
    exit(1)

# Connect to RabbitMQ
credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
connection_params = pika.ConnectionParameters(
    host=RABBITMQ_HOST,
    credentials=credentials,
    connection_attempts=5,
    retry_delay=5,
)


def on_connected(connection):
    logger.info("Connected to RabbitMQ")


connection = pika.SelectConnection(connection_params, on_open_callback=on_connected)

logger.info("Connecting to RabbitMQ attempt")
connection.ioloop.start()
