import os
import re
from glob import glob
from datetime import datetime

def read_timecodes_from_txt(txt_filepath):
    """Lit les timecodes du fichier .txt et les retourne sous forme de liste de dictionnaires."""
    timecodes = []
    with open(txt_filepath, 'r', encoding='utf-8') as file:
        lines = file.readlines()

        # Ignorer les lignes d'en-tête et toute ligne qui ne correspond pas au format attendu
        for line in lines:
            if 'Timeline Start' in line or 'Timeline End' in line or 'Source Start' in line or 'Source End' in line:
                continue  # Passer cette ligne

            # Split par des espaces pour récupérer les colonnes
            columns = line.split()
            
            # Vérification de la validité des données avant de les ajouter
            if len(columns) >= 4:
                timeline_start = columns[0]
                timeline_end = columns[1]
                source_start = columns[2]
                source_end = columns[3]

                # Vérifier que tous les timecodes sont au bon format
                try:
                    time_to_ms(timeline_start)
                    time_to_ms(timeline_end)
                    time_to_ms(source_start)
                    time_to_ms(source_end)
                except ValueError as e:
                    # Afficher la ligne et l'erreur pour diagnostiquer
                    print(f"Erreur avec la ligne : {line.strip()}")
                    print(f"Exception: {e}")
                    continue  # Si l'un des timecodes n'est pas valide, ignorer cette ligne
                
                timecodes.append({
                    'timeline_start': timeline_start,
                    'timeline_end': timeline_end,
                    'source_start': source_start,
                    'source_end': source_end,
                })
    return timecodes


def time_to_ms(time_str):
    """Convertit un timecode HH:MM:SS.ms en millisecondes (avec 3 chiffres pour les millisecondes)."""
    time_obj = datetime.strptime(time_str, "%H:%M:%S.%f")
    return int(time_obj.hour * 3600000 + time_obj.minute * 60000 + time_obj.second * 1000 + time_obj.microsecond // 1000)

def ms_to_time(ms):
    """Convertit des millisecondes en timecode H:MM:SS.ms avec deux chiffres pour les millisecondes (arrondi)."""
    hours = ms // 3600000
    minutes = (ms % 3600000) // 60000
    seconds = (ms % 60000) // 1000
    milliseconds = round(ms % 1000 / 10)  # Arrondir à 2 décimales
    
    # Vérification pour éviter que les millisecondes dépassent 1000 ou aient des valeurs comme 100
    if milliseconds == 100:
        milliseconds = 0  # Arrondir vers 0 si la valeur est proche de 1 seconde
        seconds += 1  # Ajouter une seconde

    return f"{hours}:{minutes:02}:{seconds:02}.{milliseconds:02}"  # Affichage avec 2 chiffres pour les millisecondes

def update_ass_timecodes(ass_filepath, timecodes):
    """Met à jour les timecodes dans le fichier .ass en fonction des timecodes du fichier .txt
    et applique les règles de filtrage pour conserver ou supprimer certaines lignes."""
    with open(ass_filepath, 'r', encoding='utf-8') as file:
        content = file.readlines()

    new_content = []
    previous_end_time_ms = None  # Variable pour stocker la fin de la ligne précédente

    for line in content:
        # On ne traite que les lignes de dialogue
        if line.startswith("Dialogue:"):
            parts = line.split(",", 9)  # Limiter à 9 pour ne pas couper les dialogues
            start_time = parts[1].strip()
            end_time = parts[2].strip()

            start_ms = time_to_ms(start_time)
            end_ms = time_to_ms(end_time)

            keep_line = False  # Indique si la ligne doit être conservée
            new_start_ms = start_ms
            new_end_ms = end_ms

            # Pour chaque plage de timecodes définie dans le fichier txt
            for timecode in timecodes:
                source_start_ms = time_to_ms(timecode['source_start'])
                source_end_ms = time_to_ms(timecode['source_end'])
                timeline_start_ms = time_to_ms(timecode['timeline_start'])
                timeline_end_ms = time_to_ms(timecode['timeline_end'])

                # Vérifier si la ligne correspond à la plage (cas normal) :
                # Condition 1 : son début est dans la plage source
                if source_start_ms <= start_ms < source_end_ms:
                    # Appliquer le décalage en fonction de la différence Timeline/Source
                    time_diff_ms = timeline_start_ms - source_start_ms
                    new_start_ms = start_ms + time_diff_ms
                    new_end_ms = end_ms + time_diff_ms
                    keep_line = True
                    break  # On a trouvé la plage correspondante

                # Condition 2 : accepter une ligne dont le début est jusqu’à 1000 ms avant le début de la plage
                # à condition que sa fin ne dépasse pas la fin de la plage de plus de 200 ms.
                elif source_start_ms - 1000 <= start_ms < source_start_ms:
                    if (end_ms - source_end_ms) > 200:
                        keep_line = False  # Exclure la ligne si la fin dépasse de plus de 200 ms
                    else:
                        # Appliquer le décalage en fonction de la différence Timeline/Source
                        time_diff_ms = timeline_start_ms - source_start_ms
                        new_start_ms = start_ms + time_diff_ms
                        new_end_ms = end_ms + time_diff_ms
                        keep_line = True
                    break  # On a trouvé la plage correspondante

                # Condition 3 : ligne à ignorer si son début est moins de 200 ms avant la fin de la plage
                # et que sa fin dépasse de plus de 2000 ms après la fin de la plage
                elif source_end_ms - 200 <= start_ms < source_end_ms and end_ms >= source_end_ms + 2000:
                    keep_line = False  # Ignorer cette ligne
                    print(f"Ligne ignorée (condition 3) : {line.strip()}")  # Debug log
                    break  # Exclure la ligne de cette plage

                # Nouvelle condition : Si le début de la ligne précède le début de la plage de moins de 1000 ms,
                # mais que la fin de la ligne se situe dans la plage, alors conserver la ligne.
                elif start_ms < source_start_ms and (source_start_ms - start_ms) < 1000 and end_ms <= source_end_ms:
                    keep_line = True  # Conserver cette ligne
                    print(f"Ligne conservée (condition supplémentaire) : {line.strip()}")  # Debug log
                    break  # On a trouvé la plage correspondante

            if keep_line:
                # Mettre à jour la ligne avec le timecode ajusté
                parts[1] = ms_to_time(new_start_ms)
                parts[2] = ms_to_time(new_end_ms)
                new_content.append(",".join(parts))
                previous_end_time_ms = new_end_ms  # Mettre à jour la fin de la ligne actuelle pour comparaison future
            else:
                # Ligne exclue selon les conditions
                continue
        else:
            # Les autres lignes (non-dialogues) sont conservées telles quelles
            new_content.append(line)

    # Sauvegarder les changements dans le fichier .ass dans le dossier "synced"
    modified_ass_file = os.path.join("synced", os.path.basename(ass_filepath))
    with open(modified_ass_file, 'w', encoding='utf-8') as file:
        file.writelines(new_content)
    print(f"Mis à jour : {modified_ass_file}")

def main():
    """Parcourt les fichiers .txt dans timecodes et associe les fichiers .ass correspondants depuis subtitles."""
    # Créer le dossier "synced" s'il n'existe pas
    output_dir = "synced"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Trouver les fichiers .txt dans le dossier "timecodes"
    txt_files = glob(os.path.join('timecodes', '*.txt'))

    # Trouver tous les fichiers .ass dans le dossier "subtitles"
    ass_files = glob(os.path.join('subtitles', '*.ass'))

    for txt_file in txt_files:
        # Extraire le numéro à partir du nom du fichier .txt
        txt_number = re.search(r'(\d+)', os.path.basename(txt_file)).group(1)

        # Trouver le fichier .ass correspondant (même numéro)
        ass_file = next((f for f in ass_files if re.search(r'(\d+)', os.path.basename(f)).group(1) == txt_number), None)

        if ass_file:
            print(f"Traitement du fichier {txt_file} et mise à jour de {ass_file}...")
            timecodes = read_timecodes_from_txt(txt_file)
            update_ass_timecodes(ass_file, timecodes)
        else:
            print(f"Aucun fichier .ass trouvé pour {txt_file}")

if __name__ == "__main__":
    main()
