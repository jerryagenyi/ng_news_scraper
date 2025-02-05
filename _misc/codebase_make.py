import os

def concatenate_files(output_file):
    with open(output_file, 'w') as output:
        for root, dirs, files in os.walk('.'):
            if root != './_misc':  # exclude _misc folder
                for file in files:
                    if file.endswith('.py') and file != '__init__.py':
                        file_path = os.path.join(root, file)
                        with open(file_path, 'r') as input_file:
                            output.write('# ' + file_path + '\n')
                            output.write(input_file.read())
                            output.write('\n\n')

concatenate_files('../codebase.py')