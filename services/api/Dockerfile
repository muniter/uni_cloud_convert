FROM python:3.9-buster
WORKDIR /usr/src/app
COPY requirements.txt ./
EXPOSE 8080
# Postgres client dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc
RUN pip install -r requirements.txt
# Para hacer debugging interno a la imagen
# CMD ["tail", "-f", "/dev/null"]
CMD [ "gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "app:create_app()" ]
