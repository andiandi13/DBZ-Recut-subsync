import os
import subprocess

# Dossier contenant les fichiers .ass
input_directory = 'synced'
output_directory = 'subtitles for Jartcut'

if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# Fonction pour fusionner les fichiers avec subdigest
def merge_files(merge_target, files_to_merge):
    output_path = os.path.join(output_directory, merge_target)
    if not files_to_merge:
        return
    
    command = ['python', 'subdigest.py', '-i', files_to_merge[0]]
    for file in files_to_merge[1:]:
        command += ['--merge-file', file]
    command += ['--remove-unused-styles', '-o', output_path]

    try:
        subprocess.run(command, check=True)
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
