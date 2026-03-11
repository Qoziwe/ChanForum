#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p ChanForum/db
mkdir -p ChanForum/static/uploads/avatars
mkdir -p ChanForum/static/uploads/posts

# Initialize SQLite database
python ChanForum/database_sqlite.py
