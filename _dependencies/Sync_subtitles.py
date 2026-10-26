import os
import re
from glob import glob, escape as glob_escape
from datetime import datetime

# Parent folder of the current folder
PARENT_FOLDER = os.path.dirname(os.getcwd())

# Chemins relatifs modifiés pour pointer vers le dossier parent
SUBTITLES_FOLDER = os.path.join(PARENT_FOLDER, 'subtitles')
TIMECODES_FOLDER = os.path.join(PARENT_FOLDER, 'timecodes')

# Fichier texte optionnel listant des dossiers (ou fichiers .ass) supplémentaires à analyser
# Un chemin par ligne, avec un alias optionnel après un "|" pour nommer le dossier de sortie :
#     W:\Mon dossier source très long | Alias
# Les lignes vides et celles commençant par # sont ignorées
LINKS_FILE = os.path.join(SUBTITLES_FOLDER, 'links.txt')


# --- Gestion des dossiers supplémentaires (links.txt) ---
def clean_alias(alias):
    """Rend un alias utilisable comme nom de dossier (caractères interdits remplacés par _)."""
    if not alias:
        return None
    alias = re.sub(r'[\\/:*?"<>|]', '_', alias)
    alias = alias.strip(' .')  # Windows refuse les noms finissant par un espace ou un point
    return alias or None


def read_links_file(links_filepath):
    """
    Lit links.txt : un chemin par ligne, avec un alias optionnel après un "|".
    Ignore les lignes vides et celles commençant par #.
    Retourne une liste de tuples (chemin, alias ou None).
    """
    entries = []
    if not os.path.isfile(links_filepath):
        return entries
    with open(links_filepath, 'r', encoding='utf-8-sig') as f:  # utf-8-sig gère le BOM du Bloc-notes
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            alias = None
            if '|' in line:
                # "|" est interdit dans les noms de fichiers Windows : il sépare sans ambiguïté
                line, alias_part = line.rsplit('|', 1)
                alias = clean_alias(alias_part.strip().strip('"').strip())
            path = line.strip().strip('"').strip()  # enlève les guillemets ("Copier comme chemin" en ajoute)
            if not path:
                continue
            entries.append((os.path.expandvars(path), alias))
    return entries


def collect_ass_files(root_folder):
    """
    Collecte les .ass du dossier (récursif) + ceux des chemins listés dans links.txt.
    Retourne une liste de tuples (chemin_du_fichier_ass, dossier_relatif_de_sortie).

    Les dossiers issus de links.txt sont sortis dans _links\\<nom>, où <nom> est l'alias donné
    dans links.txt, ou à défaut le nom du dossier source. Le nom est suffixé par _2, _3, ...
    si un autre dossier de links.txt porte le même nom (ou le même alias).
    """
    entries = {}  # clé = chemin réel normalisé (dédoublonnage), valeur = (chemin, dossier relatif)

    # 1) Fichiers du dossier subtitles : on garde l'arborescence d'origine
    for f in glob(os.path.join(glob_escape(root_folder), '**', '*.ass'), recursive=True):
        key = os.path.normcase(os.path.realpath(f))
        entries.setdefault(key, (f, os.path.relpath(os.path.dirname(f), root_folder)))

    # 2) Fichiers venant de links.txt, avec un nom de dossier unique par source
    assigned_names = {}   # chemin réel du dossier source -> nom attribué
    used_names = set()    # noms déjà pris (en minuscules, Windows est insensible à la casse)

    def get_unique_name(folder, alias=None):
        key = os.path.normcase(os.path.realpath(folder))
        if key in assigned_names:  # même dossier listé plusieurs fois : le premier nom/alias est gardé
            return assigned_names[key]
        base = alias or os.path.basename(os.path.abspath(folder).rstrip('\\/'))
        if not base:  # racine d'un lecteur, ex. "W:\"
            base = os.path.splitdrive(os.path.abspath(folder))[0].replace(':', '') or 'root'
        name = base
        n = 2
        while name.lower() in used_names:
            name = f"{base}_{n}"
            n += 1
        used_names.add(name.lower())
        assigned_names[key] = name
        return name

    for path, alias in read_links_file(LINKS_FILE):
        if os.path.isdir(path):
            name = get_unique_name(path, alias)
            for f in glob(os.path.join(glob_escape(path), '**', '*.ass'), recursive=True):
                inside = os.path.relpath(os.path.dirname(f), path)
                rel = os.path.join("_links", name) if inside == '.' else os.path.join("_links", name, inside)
                key = os.path.normcase(os.path.realpath(f))
                entries.setdefault(key, (f, rel))
        elif os.path.isfile(path) and path.lower().endswith('.ass'):
            name = get_unique_name(os.path.dirname(os.path.abspath(path)), alias)
            key = os.path.normcase(os.path.realpath(path))
            entries.setdefault(key, (path, os.path.join("_links", name)))
        else:
            print(f"Chemin ignoré (introuvable ou non pertinent) : {path}")

    return list(entries.values())


# Fonction pour lire les timecodes depuis un fichier texte
def read_timecodes_from_txt(txt_filepath):
    timecodes = []
    with open(txt_filepath, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        for line in lines:
            if 'Timeline Start' in line or 'Timeline End' in line or 'Source Start' in line or 'Source End' in line:
                continue
            columns = line.split()
            if len(columns) >= 4:
                try:
                    time_to_ms(columns[0])
                    time_to_ms(columns[1])
                    time_to_ms(columns[2])
                    time_to_ms(columns[3])
                except ValueError:
                    continue
                forced = False
                if len(columns) >= 5 and columns[4].lower() == 'yes':
                    forced = True
                timecodes.append({
                    'timeline_start': columns[0],
                    'timeline_end': columns[1],
                    'source_start': columns[2],
                    'source_end': columns[3],
                    'forced': forced
                })
    return timecodes

def time_to_ms(time_str):
    time_str = time_str.strip()
    is_negative = False
    
    # Gère le cas où le timecode est négatif
    if time_str.startswith('-'):
        is_negative = True
        time_str = time_str[1:]  # On enlève le signe '-' pour le parsing
        
    time_obj = datetime.strptime(time_str, "%H:%M:%S.%f")
    ms = int(time_obj.hour * 3600000 + time_obj.minute * 60000 +
             time_obj.second * 1000 + time_obj.microsecond // 1000)
    
    return -ms if is_negative else ms

def ms_to_time(ms):
    # Si le temps est négatif, on garde le signe en mémoire et on travaille en positif
    is_negative = ms < 0
    ms = abs(ms)
    
    hours = ms // 3600000
    minutes = (ms % 3600000) // 60000
    seconds = (ms % 60000) // 1000
    milliseconds = round((ms % 1000) / 10)
    
    if milliseconds == 100:
        milliseconds = 0
        seconds += 1
        if seconds == 60:
            seconds = 0
            minutes += 1
            if minutes == 60:
                minutes = 0
                hours += 1
                
    prefix = "-" if is_negative else ""
    return f"{prefix}{hours}:{minutes:02}:{seconds:02}.{milliseconds:02}"

def update_ass_timecodes(ass_filepath, timecodes, output_subfolder):
    with open(ass_filepath, 'r', encoding='utf-8') as file:
        content = file.readlines()

    # --- Synchronisation normale ---
    new_content = []
    for line in content:
        if line.startswith("Dialogue:"):
            parts = line.split(",", 9)
            start_ms = time_to_ms(parts[1].strip())
            end_ms = time_to_ms(parts[2].strip())
            keep_line = False
            new_start_ms = start_ms
            new_end_ms = end_ms

            for timecode in timecodes:
                source_start_ms = time_to_ms(timecode['source_start'])
                source_end_ms = time_to_ms(timecode['source_end'])
                timeline_start_ms = time_to_ms(timecode['timeline_start'])

                if source_start_ms <= start_ms < source_end_ms:
                    time_diff_ms = timeline_start_ms - source_start_ms
                    new_start_ms = start_ms + time_diff_ms
                    new_end_ms = end_ms + time_diff_ms
                    keep_line = True
                    break
                elif source_start_ms - 1000 <= start_ms < source_start_ms:
                    if (end_ms - source_end_ms) <= 200:
                        time_diff_ms = timeline_start_ms - source_start_ms
                        new_start_ms = start_ms + time_diff_ms
                        new_end_ms = end_ms + time_diff_ms
                        keep_line = True
                    break
                elif source_end_ms - 200 <= start_ms < source_end_ms and end_ms >= source_end_ms + 2000:
                    keep_line = False
                    break
                elif start_ms < source_start_ms and (source_start_ms - start_ms) < 1000 and end_ms <= source_end_ms:
                    keep_line = True
                    break

            if keep_line:
                parts[1] = ms_to_time(new_start_ms)
                parts[2] = ms_to_time(new_end_ms)
                new_content.append(",".join(parts))
        else:
            new_content.append(line)

    # Trie les dialogues
    dialogue_lines = [l for l in new_content if l.startswith("Dialogue:")]
    sorted_dialogues = sorted(dialogue_lines, key=lambda l: time_to_ms(l.split(",", 9)[1].strip()))
    result = []
    idx = 0
    for line in new_content:
        if line.startswith("Dialogue:"):
            result.append(sorted_dialogues[idx])
            idx += 1
        else:
            result.append(line)

    os.makedirs(output_subfolder, exist_ok=True)
    modified_ass_file = os.path.join(output_subfolder, os.path.basename(ass_filepath))

    # --- Ajout des lignes Forced sync = Yes ---
    existing_dialogues = set()
    for line in result:
        if line.startswith("Dialogue:"):
            parts = line.split(",", 9)
            key = (parts[1].strip(), parts[9].strip())
            existing_dialogues.add(key)

    for timecode in timecodes:
        if not timecode['forced']:
            continue
        source_start_ms = time_to_ms(timecode['source_start'])
        source_end_ms = time_to_ms(timecode['source_end'])
        timeline_start_ms = time_to_ms(timecode['timeline_start'])

        for line in content:
            if not line.startswith("Dialogue:"):
                continue
            parts = line.split(",", 9)
            start_ms = time_to_ms(parts[1].strip())
            end_ms = time_to_ms(parts[2].strip())
            text = parts[9].strip()

            if source_start_ms <= start_ms <= source_end_ms:
                new_start = ms_to_time(start_ms + (timeline_start_ms - source_start_ms))
                new_end = ms_to_time(end_ms + (timeline_start_ms - source_start_ms))
                key = (new_start, text)
                if key not in existing_dialogues:
                    new_line = ",".join(parts[:1] + [new_start, new_end] + parts[3:])
                    result.append(new_line + "\n")
                    existing_dialogues.add(key)

    # Tri final
    dialogue_lines = [l for l in result if l.startswith("Dialogue:")]
    sorted_dialogues = sorted(dialogue_lines, key=lambda l: time_to_ms(l.split(",", 9)[1].strip()))
    final_result = []
    idx = 0
    for line in result:
        if line.startswith("Dialogue:"):
            final_result.append(sorted_dialogues[idx])
            idx += 1
        else:
            final_result.append(line)

    with open(modified_ass_file, 'w', encoding='utf-8') as file:
        file.writelines(final_result)

    print(f"Updated: {modified_ass_file}")


# --- Fonction principale ---
def main():
    # (chemin .ass, dossier relatif de sortie) : subtitles + chemins listés dans links.txt
    ass_entries = collect_ass_files(SUBTITLES_FOLDER)
    txt_files = glob(os.path.join(TIMECODES_FOLDER, '*', '*.txt'))

    for txt_file in txt_files:
        subfolder = os.path.basename(os.path.dirname(txt_file))
        txt_number_match = re.search(r'(\d+)', os.path.basename(txt_file))
        if not txt_number_match:
            continue
        txt_number = txt_number_match.group(1)

        matching_ass_files = [(f, rel) for f, rel in ass_entries
                              if re.search(r'(\d+)', os.path.basename(f))
                              and re.search(r'(\d+)', os.path.basename(f)).group(1) == txt_number]

        if matching_ass_files:
            timecodes = read_timecodes_from_txt(txt_file)
            for ass_file, relative_dir in matching_ass_files:
                if relative_dir == '.' or relative_dir == '':
                    output_subfolder = os.path.join(PARENT_FOLDER, "synced", subfolder)
                else:
                    output_subfolder = os.path.join(PARENT_FOLDER, "synced", relative_dir, subfolder)

                update_ass_timecodes(ass_file, timecodes, output_subfolder)
        else:
            print(f"No matching .ass file for {txt_file}")


if __name__ == "__main__":
    main()
