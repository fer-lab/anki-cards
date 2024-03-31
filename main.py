import os
import ast
import questionary
import subprocess

def check_import_and_variable(file_path, library, variable_name):
    """
    Checks if the file at `file_path` imports the specified library
    and defines the given variable.

    Returns the value of the variable if both conditions are met, None otherwise.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    tree = ast.parse(content, filename=file_path)
    imports_library = False
    variable_value = None

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                if alias.name == library or getattr(node, 'module', '') == library:
                    imports_library = True
                    break
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == variable_name:
                    # Handling both Python versions < 3.8 and >= 3.8
                    variable_value = node.value.s if isinstance(node.value, ast.Str) else node.value.value
                    break

    if imports_library and variable_value is not None:
        return variable_value
    return None


def list_sibling_directories():
    """
    List all directories that are in the same level as the executed file,
    excluding those starting with '.' and named 'anki'.
    """
    executed_file_directory = os.path.dirname(os.path.abspath(__file__))
    all_entries = os.listdir(executed_file_directory)

    sibling_directories = [entry for entry in all_entries
                           if os.path.isdir(os.path.join(executed_file_directory, entry))
                           and not entry.startswith(".")
                           and entry != "anki"]

    return sibling_directories


def main():
    files_info = {}
    directories = list_sibling_directories()

    for directory in directories:
        dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), directory)
        for filename in os.listdir(dir_path):
            if filename.endswith('.py') and not filename.startswith('.') and filename != 'anki':
                full_path = os.path.join(dir_path, filename)
                value = check_import_and_variable(full_path, 'genanki', 'deck_name')
                if value is not None:
                    # Combine the directory name and file name for display
                    display_name = f"{directory}/{filename}"
                    files_info[display_name] = full_path

    if not files_info:
        print("No files found matching the criteria.")
        return

    # We use questionary to allow the user to select a file, displaying directory and name
    display_name_to_execute = questionary.select(
        "Choose a file to execute:",
        choices=list(files_info.keys())
    ).ask()

    # We execute the selected file using its full path
    if display_name_to_execute:
        file_to_execute = files_info[display_name_to_execute]
        print(f"Executing {display_name_to_execute}...")
        subprocess.run(["python3", file_to_execute], check=True)
    else:
        print("No file was selected.")

if __name__ == "__main__":
    main()
