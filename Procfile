release: python manage.py migrate
web: gunicorn -c gunicorn.conf.py clabot.asgi:application --log-file -
worker: python manage.py db_worker
