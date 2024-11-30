#!/bin/sh
set -e

echo "Starting entrypoint.sh"

if [ "$PG_HOST" = "pg_db" ]
then
    echo "Waiting for postgresql..."

    while ! nc -z $PG_HOST $PG_PORT; do
        sleep 0.1
    done

    echo "Postgresql started"
fi
chmod 0777 /var/log/gunicorn/tentron_errors.log
# Ensure tentron has ownership over the necessary directories
if [ "$(ls -ld /var/log/gunicorn | awk '{print $3}')" != 'tentron' ]; then
    chown -R tentron:tentron /var/log/gunicorn
    
    echo "Changed ownership of /var/log/gunicorn"
fi

# change ownership of media and static files
if [ "$(ls -ld /home/app/media | awk '{print $3}')" != 'tentron' ]; then
    chown -R tentron:tentron /home/app/media
    echo "Changed ownership of /home/app/media"
fi

if [ "$(ls -ld /home/app/static | awk '{print $3}')" != 'tentron' ]; then
    chown -R tentron:tentron /home/app/static
    echo "Changed ownership of /home/app/static"
fi

# Set celery log file permissions
chmod 0777  /var/log/celery/celery.log



# set an appropriate umask (if one isn't set already)
um="$(umask)"
if [ "$um" = '0022' ]; then
	umask 0077
fi

# run commands as tentron user
gosu tentron python manage.py migrate
gosu tentron python manage.py collectstatic --no-input --clear
echo "Collecting static files...finished"
gosu tentron python manage.py update_index
echo "Updating search index...finished"

# Start Celery worker as celery user
gosu celery celery -A tentron worker --loglevel=info &

# Start Gunicorn as tentron user
exec gosu tentron "$@"
