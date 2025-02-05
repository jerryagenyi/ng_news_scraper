#!/bin/bash

cd ..
tree -a -I 'venv|_misc|README.md|__init__.py*|__pycache__|db_backups|.DS_Store|.git|.gitignore' > _misc/project_structure_output_tree.txt