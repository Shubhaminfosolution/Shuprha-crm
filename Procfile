web: gunicorn Company.wsgi --log-file - --timeout 120
worker: celery -A Company worker --beat --loglevel=info