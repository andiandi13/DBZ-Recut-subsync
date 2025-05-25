import os
import re
from glob import glob
from datetime import datetime

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
                timecodes.append({
                    'timeline_start': columns[0],
                    'timeline_end': columns[1],
                    'source_start': columns[2],
                    'source_end': columns[3],
                })
    return timecodes

def time_to_ms(time_str):
    time_obj = datetime.strptime(time_str, "%H:%M:%S.%f")
    return int(time_obj.hour * 3600000 + time_obj.minute * 60000 +
               time_obj.second * 1000 + time_obj.microsecond // 1000)

def ms_to_time(ms):
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
    return f"{hours}:{minutes:02}:{seconds:02}.{milliseconds:02}"

def update_ass_timecodes(ass_filepath, timecodes, output_subfolder):
    with open(ass_filepath, 'r', encoding='utf-8') as file:
        content = file.readlines()

    new_content = []
    for line in content:
        if line.startswith("Dialogue:"):
            parts = line.split(",", 9)
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

                if source_start_ms <= start_ms < source_end_ms:
                    time_diff_ms = timeline_start_ms - source_start_ms
                    new_start_ms = start_ms + time_diff_ms
                    new_end_ms = end_ms + time_diff_ms
                    keep_line = True
                    break
                elif source_start_ms - 1000 <= start_ms < source_start_ms:
                    if (end_ms - source_end_ms) > 200:
                        keep_line = False
                    else:
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

    os.makedirs(output_subfolder, exist_ok=True)
    modified_ass_file = os.path.join(output_subfolder, os.path.basename(ass_filepath))
    with open(modified_ass_file, 'w', encoding='utf-8') as file:
        file.writelines(result)
    print(f"Mis à jour : {modified_ass_file}")

def main():
    ass_files = glob(os.path.join('subtitles', '*.ass'))
    txt_files = glob(os.path.join('timecodes', '*', '*.txt'))  # Récupère les .txt dans les sous-dossiers

    for txt_file in txt_files:
        subfolder = os.path.basename(os.path.dirname(txt_file))  # nom du sous-dossier
        txt_number_match = re.search(r'(\d+)', os.path.basename(txt_file))
        if not txt_number_match:
            continue
        txt_number = txt_number_match.group(1)

        ass_file = next((f for f in ass_files if re.search(r'(\d+)', os.path.basename(f)) and re.search(r'(\d+)', os.path.basename(f)).group(1) == txt_number), None)
        if ass_file:
            print(f"Traitement : {txt_file} -> {ass_file}")
            timecodes = read_timecodes_from_txt(txt_file)
            output_subfolder = os.path.join("synced", subfolder)
            update_ass_timecodes(ass_file, timecodes, output_subfolder)
        else:
            print(f"Aucun fichier .ass correspondant pour {txt_file}")

if __name__ == "__main__":
    main()
