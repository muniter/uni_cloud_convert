FROM python:3.9-buster
WORKDIR /usr/src/app
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY . .
CMD [ "python", "app.py" ]