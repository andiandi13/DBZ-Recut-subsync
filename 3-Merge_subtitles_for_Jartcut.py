import os
import subprocess

# Dossiers
input_directory = 'synced'
output_directory = 'subtitles for Jartcut'

# Création du dossier de sortie s'il n'existe pas
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# Fonction pour sécuriser les chemins avec des espaces
def quote(path):
    return f'"{path}"' if ' ' in path else path

# Fonction pour fusionner les fichiers avec subdigest
def merge_files(merge_target, files_to_merge):
    output_path = os.path.join(output_directory, merge_target)
    if not files_to_merge:
        return

    # Construction de la commande avec guillemets si nécessaire
    command = f'python subdigest.py -i {quote(files_to_merge[0])}'
    for file in files_to_merge[1:]:
        command += f' --merge-file {quote(file)}'
    command += f' --remove-unused-styles -o {quote(output_path)}'

    try:
        subprocess.run(command, shell=True, check=True)
        print(f"Fusion réussie pour {output_path}")
    except subprocess.CalledProcessError:
        print(f"Erreur lors de la fusion de {output_path}")

# Fonction principale
def main():
    for root, dirs, _ in os.walk(input_directory):
        if root == input_directory:
            for subfolder in dirs:
                subfolder_path = os.path.join(input_directory, subfolder)
                ass_files = [os.path.join(subfolder_path, f)
                             for f in os.listdir(subfolder_path)
                             if f.endswith('.ass')]
                if ass_files:
                    output_filename = f"{subfolder}.ass"
                    print(f"Fusion avec subdigest pour le dossier '{subfolder}'")
                    merge_files(output_filename, ass_files)

if __name__ == '__main__':
    main()
