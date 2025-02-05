#run_scripts.sh
#!/bin/bash

# Run the codebase creation script.
# This will create updated single-file codebase to share with AI assistant for context
python ../_misc/codebase_make.py

# Run the database backup script
python backup_db.py