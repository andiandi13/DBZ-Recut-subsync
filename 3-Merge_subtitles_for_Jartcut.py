import os
import re
from datetime import datetime

# Dossier contenant les fichiers .ass
input_directory = 'synced'
output_directory = 'subtitles for Jartcut'

if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# Fonction pour parser un fichier .ass en sections
def parse_ass_file(path):
    with open(path, 'r', encoding='utf-8-sig') as f:
        lines = f.readlines()

    sections = {}
    current_section = None
    for line in lines:
        line = line.strip('\n')
        if line.startswith('[') and line.endswith(']'):
            current_section = line
            sections[current_section] = []
        elif current_section:
            sections[current_section].append(line)
    return sections

# Fonction pour extraire l'heure de début d'une ligne Dialogue
def get_start_time(dialogue_line):
    match = re.match(r'Dialogue: [^,]*,([^,]*)', dialogue_line)
    if match:
        return datetime.strptime(match.group(1), '%H:%M:%S.%f')
    return datetime.min

# Fonction de fusion proprement dite
def merge_ass_files(output_filename, ass_paths):
    headers = {}
    events = []

    for path in ass_paths:
        ass = parse_ass_file(path)
        for section, lines in ass.items():
            if section == '[Events]':
                for line in lines:
                    if line.startswith('Dialogue:'):
                        events.append(line)
            else:
                # Ne conserve qu'un seul exemplaire des autres sections
                if section not in headers:
                    headers[section] = lines

    # Tri des dialogues
    events.sort(key=get_start_time)

    # Reconstruction du fichier final
    output_path = os.path.join(output_directory, output_filename)
    with open(output_path, 'w', encoding='utf-8-sig') as f:
        for section in ['[Script Info]', '[V4+ Styles]']:
            if section in headers:
                f.write(section + '\n')
                for line in headers[section]:
                    f.write(line + '\n')
                f.write('\n')

        f.write('[Events]\n')
        f.write('Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n')
        for line in events:
            f.write(line + '\n')
    print(f"Fusion réussie avec tri : {output_path}")

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
                    print(f"Fusion avec tri des dialogues dans le dossier '{subfolder}'")
                    merge_ass_files(output_filename, ass_files)

if __name__ == '__main__':
    main()
