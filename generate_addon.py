import os
import shutil

addon_name = "test_addon"
source_dir = './template/'
dest_dir = f'./{addon_name}/'

# Automatically determine the capitalized replacement without spaces
addon_name_capitalized = ''.join(word.capitalize() for word in addon_name.split('_'))

search_replace_pairs = {
    "template": addon_name,
    "Template": addon_name_capitalized
}

def replace_in_file(file_path, search_replace_pairs):
    with open(file_path, 'r') as file:
        content = file.read()
    for search, replace in search_replace_pairs.items():
        content = content.replace(search, replace)
    with open(file_path, 'w') as file:
        file.write(content)

def process_directory(source_dir, dest_dir, search_replace_pairs):
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    
    for root, dirs, files in os.walk(source_dir):
        relative_path = os.path.relpath(root, source_dir)
        dest_path = os.path.join(dest_dir, relative_path)
        
        if not os.path.exists(dest_path):
            os.makedirs(dest_path)
        
        for file in files:
            src_file = os.path.join(root, file)
            dest_file = os.path.join(dest_path, file)
            shutil.copy2(src_file, dest_file)
            replace_in_file(dest_file, search_replace_pairs)

def generate_files():
    process_directory(source_dir, dest_dir, search_replace_pairs)
    
    # Process the entry.py file at the same level as this script
    entry_file = 'entry.py'
    if os.path.exists(entry_file):
        replace_in_file(entry_file, search_replace_pairs)

generate_files()
