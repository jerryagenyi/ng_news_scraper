#!/bin/bash

# Activate virtual environment
source ../venv/bin/activate

# Set executable permissions
chmod +x run_scripts.sh

# Run the codebase creation script (if needed)
# python3 ../_misc/codebase_make.py

# Run the database backup script
PYTHONPATH=/Users/jeremiah/Projects/ng_news_scraper python3 backup_db.py

# List recent backups
echo -e "\n📁 Recent backups:"
ls -lh *.sql.gz | tail -n 5