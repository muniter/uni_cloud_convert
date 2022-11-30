gunicorn -b :$PORT -w 1 "server:app" &
python app.py
