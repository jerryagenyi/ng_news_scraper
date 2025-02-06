#!/bin/bash
# Shows current main directory structure

tree -a -I 'venv|README.md|__init__.py*|__pycache__|db_backups|.DS_Store|.git|.gitignore' > tree.txt