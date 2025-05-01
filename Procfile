release: python manage.py migrate
web: memray run --native --follow-fork -o /tmp/memray-gunicorn.bin -f -m gunicorn -c gunicorn.conf.py clabot.asgi:application --log-file -
worker: python manage.py db_worker
