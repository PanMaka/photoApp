#!/bin/bash

echo "Building the k29photo database..."

# Running standard psql commands. 
# It connects to the default 'postgres' database just to execute the creation commands.
psql -d postgres -c "DROP DATABASE IF EXISTS k29photo_db;"
psql -d postgres -c "CREATE DATABASE k29photo_db;"

# Build the schema inside the new database
psql -d k29photo_db -f schema.sql

echo "Database successfully initialized!"
echo "Starting Flask server..."

export FLASK_APP=app.py
export FLASK_ENV=development
python3 -m flask run