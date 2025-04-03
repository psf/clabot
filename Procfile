release: python manage.py migrate
web: gunicorn -c config/gunicorn.conf.py clabot.asgi:application --log-file -
