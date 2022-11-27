FROM python:3.9-buster
WORKDIR /usr/src/app
COPY requirements.txt ./

COPY ./ ./
# Postgres client dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc
RUN pip install -r requirements.txt
# Para hacer debugging interno a la imagen
# CMD ["tail", "-f", "/dev/null"]
CMD [ "gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:create_app()" ]
