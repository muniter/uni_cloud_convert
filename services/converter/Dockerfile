FROM python:3.9-buster
WORKDIR /usr/src/app
COPY requirements.txt ./
# Postgres client dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    ffmpeg
RUN pip install -r requirements.txt
CMD [ "celery", "-A", "app", "worker", "--loglevel=info" ]
