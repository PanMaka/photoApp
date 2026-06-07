#!/bin/bash

echo "Setting up k29photo database..."

psql -U postgres -d postgres -c "DROP DATABASE IF EXISTS k29photo;"
psql -U postgres -d postgres -c "CREATE DATABASE k29photo;"
psql -U postgres -d k29photo -f schema.sql

echo "Populating mock data..."
python3 fill_db.py

echo "Starting Flask server..."
flask run