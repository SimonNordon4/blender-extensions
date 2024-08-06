import tkinter as tk
from tkinter import messagebox, filedialog
import os
import shutil
import zipfile
import subprocess


#################### Addon Generation Logic ####################


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

def generate_files(addon_name):
    source_dir = './template/'
    dest_dir = f'./{addon_name}/'

    # Automatically determine the capitalized replacement without spaces
    addon_name_capitalized = ''.join(word.capitalize() for word in addon_name.split('_'))

    search_replace_pairs = {
        "template": addon_name,
        "Template": addon_name_capitalized
    }
    process_directory(source_dir, dest_dir, search_replace_pairs)
    
    # Process the entry.py file at the same level as this script
    entry_file = 'entry.py'
    if os.path.exists(entry_file):
        replace_in_file(entry_file, search_replace_pairs)

def create_addon_from_template():
    addon_name = addon_name_entry.get()
    if not addon_name:
        messagebox.showwarning("Input Required", "Please enter an addon name.")
        return
    # Logic for creating addon from template
    # set the addon name to lower case, remove spaces and replace with _
    addon_name = addon_name.lower().replace(' ', '_')
    generate_files(addon_name)
    messagebox.showinfo("Success", f"Addon '{addon_name}' created from template.")

def zip_addon():
    base_dir = os.getcwd()  # Directory where your add-ons are located

    for item in os.listdir(base_dir):
        item_path = os.path.join(base_dir, item)
        if os.path.isdir(item_path) and item != "template":
            zip_name = os.path.join(base_dir, f"{item}.zip")
            if os.path.exists(zip_name):
                os.remove(zip_name)  # Remove the existing zip file if it exists
            with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(item_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, base_dir)
                        zipf.write(file_path, arcname)
    
    messagebox.showinfo("Success", "All addons zipped successfully.")


def build_blender_extensions():
    base_dir = os.getcwd()
    command = f"blender --command extension server-generate --repo-dir={base_dir} --html"
    try:
        subprocess.run(command, check=True, shell=True)
        messagebox.showinfo("Success", "Blender extensions built successfully.")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"Failed to build Blender extensions:\n{e}")

# Create the main window
root = tk.Tk()
root.title("Addon Manager")

# Create a frame for "Create new Addon"
frame_create_addon = tk.LabelFrame(root, text="Create new Addon", padx=10, pady=10)
frame_create_addon.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

# Add a text field with label to the first frame
tk.Label(frame_create_addon, text="Addon Name:").grid(row=0, column=0, padx=10, pady=10)
addon_name_entry = tk.Entry(frame_create_addon)
addon_name_entry.grid(row=0, column=1, padx=10, pady=10)

# Add the "Create Addon from Template" button to the first frame
create_button = tk.Button(frame_create_addon, text="Create Addon from Template", command=create_addon_from_template)
create_button.grid(row=1, column=0, columnspan=2, padx=10, pady=5)

# Create a frame for "Build Extensions"
frame_build_extensions = tk.LabelFrame(root, text="Build Extensions", padx=10, pady=10)
frame_build_extensions.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

# Add the "Zip Addon" button to the second frame
zip_button = tk.Button(frame_build_extensions, text="Zip All Addons", command=zip_addon)
zip_button.grid(row=1, column=0, columnspan=3, padx=10, pady=5)

# Add the "Build Blender Extensions" button to the second frame
build_button = tk.Button(frame_build_extensions, text="Build Blender Extensions Index", command=build_blender_extensions)
build_button.grid(row=2, column=0, columnspan=3, padx=10, pady=5)

# Run the application
root.mainloop()