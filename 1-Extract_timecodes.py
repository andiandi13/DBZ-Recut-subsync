import os
import glob
import xml.etree.ElementTree as ET
from datetime import timedelta

# Dossier contenant les fichiers .kdenlive
KDENLIVE_FOLDER = os.path.join(os.getcwd(), 'kdenlive')
# Dossier de sortie des fichiers txt
TIMECODES_FOLDER = os.path.join(os.getcwd(), 'timecodes')

# Vérifier et créer le dossier timecodes si nécessaire
if not os.path.exists(TIMECODES_FOLDER):
    os.makedirs(TIMECODES_FOLDER)

FRAME_OFFSET = 0.042  # 42 ms en secondes

def timecode_to_seconds(timecode):
    hh, mm, ss_ms = timecode.split(':')
    ss, ms = ss_ms.split('.')
    return int(hh) * 3600 + int(mm) * 60 + int(ss) + int(ms) / 1000

def seconds_to_timecode(seconds):
    td = timedelta(seconds=seconds)
    h, m, s = td.seconds // 3600, (td.seconds % 3600) // 60, td.seconds % 60
    ms = td.microseconds // 1000
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"

def process_kdenlive_file(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()

    video_synced_sources = {}

    for chain in root.findall(".//chain"):
        resource_elem = chain.find(".//property[@name='resource']")
        if resource_elem is not None and "video synced" in resource_elem.text.lower():
            chain_id = chain.get("id")
            resource_filename = os.path.basename(resource_elem.text.strip())
            audio_source_name, _ = os.path.splitext(resource_filename)
            video_synced_sources[chain_id] = audio_source_name

    for producer in root.findall(".//producer"):
        resource_elem = producer.find(".//property[@name='resource']")
        if resource_elem is not None and "video synced" in resource_elem.text.lower():
            producer_id = producer.get("id")
            resource_filename = os.path.basename(resource_elem.text.strip())
            audio_source_name, _ = os.path.splitext(resource_filename)
            video_synced_sources[producer_id] = audio_source_name

    grouped_results = {source: [] for source in video_synced_sources.values()}

    for playlist in root.findall(".//playlist"):
        if playlist.get("id") == "main_bin":
            continue

        timeline_position = 0.0
        clip_count = 0

        for element in playlist:
            if element.tag == "blank":
                blank_length = element.get("length")
                blank_duration = timecode_to_seconds(blank_length)
                timeline_position += blank_duration
            elif element.tag == "entry":
                producer = element.get("producer")
                clip_in_str = element.get("in")
                clip_out_str = element.get("out")

                if clip_in_str is None or clip_out_str is None:
                    continue

                clip_in = timecode_to_seconds(clip_in_str)
                clip_out = timecode_to_seconds(clip_out_str)
                clip_duration = clip_out - clip_in

                clip_count += 1
                offset = FRAME_OFFSET * clip_count

                timeline_start = timeline_position + offset
                timeline_end = timeline_start + clip_duration

                has_asubcut = (
                    producer in video_synced_sources and
                    any(
                        filt.find("./property[@name='mlt_service']") is not None and
                        filt.find("./property[@name='mlt_service']").text == "avfilter.asubcut"
                        for filt in element.findall("filter")
                    )
                )

                if not has_asubcut and producer in video_synced_sources:
                    audio_source = video_synced_sources[producer]
                    grouped_results[audio_source].append({
                        'timeline_start': timeline_start,
                        'timeline_end': timeline_end,
                        'source_in': clip_in,
                        'source_out': clip_out
                    })

                timeline_position += clip_duration

    return grouped_results

def main():
    if os.path.isdir(KDENLIVE_FOLDER):
        for file_path in glob.glob(os.path.join(KDENLIVE_FOLDER, "*.kdenlive")):
            kdenlive_name = os.path.splitext(os.path.basename(file_path))[0]
            output_subfolder = os.path.join(TIMECODES_FOLDER, kdenlive_name)
            os.makedirs(output_subfolder, exist_ok=True)

            file_results = process_kdenlive_file(file_path)
            for audio_source, clips in file_results.items():
                if not clips:
                    continue

                sorted_clips = sorted(clips, key=lambda clip: clip['timeline_start'])
                output_lines = [f"{'Timeline Start':<16} {'Timeline End':<16} {'Source Start':<16} {'Source End':<16}"]

                for clip in sorted_clips:
                    line = f"{seconds_to_timecode(clip['timeline_start']):<16} {seconds_to_timecode(clip['timeline_end']):<16} " \
                           f"{seconds_to_timecode(clip['source_in']):<16} {seconds_to_timecode(clip['source_out']):<16}"
                    output_lines.append(line)

                output_file = os.path.join(output_subfolder, f"{audio_source}.txt")
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write("\n".join(output_lines))
                print(f"Timecodes pour '{audio_source}' enregistrés dans : {output_file}")
    else:
        print(f"Le dossier 'kdenlive' n'existe pas dans le répertoire courant.")

if __name__ == "__main__":
    main()
