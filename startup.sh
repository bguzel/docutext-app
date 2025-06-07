#!/bin/sh

# This script will run our database migrations and then start the Gunicorn server.

echo "--- Running Database Migrations ---"
# Run the Python command to create the database tables.
# The 'with app.app_context()' is crucial.
python -c "from app import app, db; app.app_context().push(); db.create_all()"
echo "--- Migrations Complete ---"

echo "--- Starting Gunicorn Server ---"
# Start the Gunicorn server (this is the command from our original Dockerfile).
exec gunicorn --workers 1 --worker-class gevent --bind 0.0.0.0:10000 app:app