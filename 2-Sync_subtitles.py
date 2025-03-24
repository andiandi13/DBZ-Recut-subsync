import os
import re
from glob import glob
from datetime import datetime

def read_timecodes_from_txt(txt_filepath):
    """Lit les timecodes du fichier .txt et les retourne sous forme de liste de dictionnaires."""
    timecodes = []
    with open(txt_filepath, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        # Ignorer les lignes d'en-tête et celles ne correspondant pas au format attendu
        for line in lines:
            if 'Timeline Start' in line or 'Timeline End' in line or 'Source Start' in line or 'Source End' in line:
                continue
            columns = line.split()
            if len(columns) >= 4:
                timeline_start = columns[0]
                timeline_end = columns[1]
                source_start = columns[2]
                source_end = columns[3]
                try:
                    time_to_ms(timeline_start)
                    time_to_ms(timeline_end)
                    time_to_ms(source_start)
                    time_to_ms(source_end)
                except ValueError as e:
                    print(f"Erreur avec la ligne : {line.strip()}")
                    print(f"Exception: {e}")
                    continue
                timecodes.append({
                    'timeline_start': timeline_start,
                    'timeline_end': timeline_end,
                    'source_start': source_start,
                    'source_end': source_end,
                })
    return timecodes

def time_to_ms(time_str):
    """Convertit un timecode HH:MM:SS.ms en millisecondes."""
    time_obj = datetime.strptime(time_str, "%H:%M:%S.%f")
    return int(time_obj.hour * 3600000 +
               time_obj.minute * 60000 +
               time_obj.second * 1000 +
               time_obj.microsecond // 1000)

def ms_to_time(ms):
    """
    Convertit des millisecondes en timecode H:MM:SS.ms
    avec deux chiffres pour les millisecondes (arrondi).
    """
    hours = ms // 3600000
    minutes = (ms % 3600000) // 60000
    seconds = (ms % 60000) // 1000
    # On arrondit les millisecondes à deux chiffres (i.e. 1/100 de seconde)
    milliseconds = round((ms % 1000) / 10)
    # Gestion du cas où l'arrondi atteint 100 (soit 1 seconde)
    if milliseconds == 100:
        milliseconds = 0
        seconds += 1
        if seconds == 60:
            seconds = 0
            minutes += 1
            if minutes == 60:
                minutes = 0
                hours += 1
    return f"{hours}:{minutes:02}:{seconds:02}.{milliseconds:02}"

def update_ass_timecodes(ass_filepath, timecodes):
    """
    Met à jour les timecodes dans le fichier .ass en fonction des timecodes du fichier .txt
    et applique les règles de filtrage pour conserver ou supprimer certaines lignes.
    Enfin, les lignes de dialogue sont triées par ordre chronologique.
    """
    with open(ass_filepath, 'r', encoding='utf-8') as file:
        content = file.readlines()

    new_content = []
    # On va traiter chaque ligne. Les lignes débutant par "Dialogue:" seront modifiées.
    for line in content:
        if line.startswith("Dialogue:"):
            parts = line.split(",", 9)  # Limiter à 9 pour ne pas couper les dialogues
            start_time = parts[1].strip()
            end_time = parts[2].strip()
            start_ms = time_to_ms(start_time)
            end_ms = time_to_ms(end_time)
            keep_line = False
            new_start_ms = start_ms
            new_end_ms = end_ms

            for timecode in timecodes:
                source_start_ms = time_to_ms(timecode['source_start'])
                source_end_ms = time_to_ms(timecode['source_end'])
                timeline_start_ms = time_to_ms(timecode['timeline_start'])
                timeline_end_ms = time_to_ms(timecode['timeline_end'])
                # Condition 1 : début dans la plage source
                if source_start_ms <= start_ms < source_end_ms:
                    time_diff_ms = timeline_start_ms - source_start_ms
                    new_start_ms = start_ms + time_diff_ms
                    new_end_ms = end_ms + time_diff_ms
                    keep_line = True
                    break
                # Condition 2 : début jusqu’à 1000 ms avant la plage
                elif source_start_ms - 1000 <= start_ms < source_start_ms:
                    if (end_ms - source_end_ms) > 200:
                        keep_line = False
                    else:
                        time_diff_ms = timeline_start_ms - source_start_ms
                        new_start_ms = start_ms + time_diff_ms
                        new_end_ms = end_ms + time_diff_ms
                        keep_line = True
                    break
                # Condition 3 : ligne à ignorer si début proche de la fin de la plage et fin trop tardive
                elif source_end_ms - 200 <= start_ms < source_end_ms and end_ms >= source_end_ms + 2000:
                    keep_line = False
                    print(f"Ligne ignorée (condition 3) : {line.strip()}")
                    break
                # Condition supplémentaire
                elif start_ms < source_start_ms and (source_start_ms - start_ms) < 1000 and end_ms <= source_end_ms:
                    keep_line = True
                    print(f"Ligne conservée (condition supplémentaire) : {line.strip()}")
                    break

            if keep_line:
                parts[1] = ms_to_time(new_start_ms)
                parts[2] = ms_to_time(new_end_ms)
                new_content.append(",".join(parts))
            # Sinon, la ligne est ignorée
        else:
            new_content.append(line)

    # Tri des lignes de dialogue par ordre chronologique
    # On remplace chaque ligne de dialogue par la suivante dans l'ordre trié,
    # tout en préservant les autres lignes dans leur position.
    dialogue_lines = [line for line in new_content if line.startswith("Dialogue:")]
    sorted_dialogues = sorted(dialogue_lines, key=lambda l: time_to_ms(l.split(",", 9)[1].strip()))
    result = []
    dialogue_index = 0
    for line in new_content:
        if line.startswith("Dialogue:"):
            result.append(sorted_dialogues[dialogue_index])
            dialogue_index += 1
        else:
            result.append(line)

    # Sauvegarde dans le dossier "synced"
    modified_ass_file = os.path.join("synced", os.path.basename(ass_filepath))
    with open(modified_ass_file, 'w', encoding='utf-8') as file:
        file.writelines(result)
    print(f"Mis à jour : {modified_ass_file}")

def main():
    """Parcourt les fichiers .txt dans 'timecodes' et associe les fichiers .ass correspondants dans 'subtitles'."""
    output_dir = "synced"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    txt_files = glob(os.path.join('timecodes', '*.txt'))
    ass_files = glob(os.path.join('subtitles', '*.ass'))

    for txt_file in txt_files:
        txt_number = re.search(r'(\d+)', os.path.basename(txt_file)).group(1)
        ass_file = next((f for f in ass_files if re.search(r'(\d+)', os.path.basename(f)).group(1) == txt_number), None)
        if ass_file:
            print(f"Traitement du fichier {txt_file} et mise à jour de {ass_file}...")
            timecodes = read_timecodes_from_txt(txt_file)
            update_ass_timecodes(ass_file, timecodes)
        else:
            print(f"Aucun fichier .ass trouvé pour {txt_file}")

if __name__ == "__main__":
    main()
