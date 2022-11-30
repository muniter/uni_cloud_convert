FROM python:3.9-buster
WORKDIR /usr/src/app
# Postgres client dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    ffmpeg
COPY ./* ./
RUN pip install -r requirements.txt
CMD [ "bash", "./startup.sh"]
