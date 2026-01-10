import os
import subprocess
import re

# Parent folder of the current folder
PARENT_FOLDER = os.path.dirname(os.getcwd())

# Dossiers dans le parent folder
input_directory = os.path.join(PARENT_FOLDER, 'synced')
output_directory = os.path.join(PARENT_FOLDER, 'subtitles for DBZ Recut')

# Création du dossier de sortie s'il n'existe pas
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# Fonction pour sécuriser les chemins avec des espaces
def quote(path):
    return f'"{path}"' if ' ' in path else path

# Fonction pour nettoyer les styles en double dans un fichier .ass
def deduplicate_styles(file_path):
    with open(file_path, "r", encoding="utf-8-sig") as f:
        lines = f.readlines()

    in_styles = False
    seen = set()
    cleaned_lines = []

    for line in lines:
        if line.strip().startswith("[V4+ Styles]"):
            in_styles = True
            cleaned_lines.append(line)
            continue

        if in_styles:
            if line.strip().startswith("Format:"):
                cleaned_lines.append(line)
                continue
            if line.strip().startswith("Style:"):
                if line not in seen:
                    seen.add(line)
                    cleaned_lines.append(line)
                continue
            if line.strip().startswith("["):
                in_styles = False
                cleaned_lines.append(line)
                continue

        cleaned_lines.append(line)

    with open(file_path, "w", encoding="utf-8-sig") as f:
        f.writelines(cleaned_lines)

# Fonction pour fusionner et trier les fichiers avec subdigest
def merge_files(merge_target, files_to_merge):
    output_path = os.path.join(output_directory, merge_target)
    if not files_to_merge:
        return

    command = f'python subdigest.py -i {quote(files_to_merge[0])}'
    for file in files_to_merge[1:]:
        command += f' --merge-file {quote(file)}'

    command += f' --remove-unused-styles --selection-set-expr "True" --sort-field start ASC -o {quote(output_path)}'

    try:
        subprocess.run(command, shell=True, check=True)
        deduplicate_styles(output_path)
        print(f"Merge successful for {os.path.basename(output_path)}")
    except subprocess.CalledProcessError:
        print(f"Error while merging {output_path}")

# Fonction principale
def main():
    for root, dirs, files in os.walk(input_directory):
        ass_files = [os.path.join(root, f) for f in files if f.endswith('.ass')]
        if ass_files:
            # Chemin relatif depuis input_directory
            rel_path = os.path.relpath(root, input_directory)

            # Suppression du dossier parent direct des .ass
            parts = [] if rel_path == "." else rel_path.split(os.sep)
            parts = parts[:-1]

            output_subfolder = os.path.join(output_directory, *parts)

            os.makedirs(output_subfolder, exist_ok=True)

            # Nom du fichier de sortie
            output_filename = os.path.basename(root) + '.ass'

            merge_files(os.path.join(*parts, output_filename), ass_files)

if __name__ == '__main__':
    main()
