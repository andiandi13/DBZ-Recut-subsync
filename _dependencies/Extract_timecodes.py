import os
import glob
import xml.etree.ElementTree as ET
from datetime import timedelta

PARENT_FOLDER = os.path.dirname(os.getcwd())
KDENLIVE_FOLDER = os.path.join(PARENT_FOLDER, 'kdenlive')
TIMECODES_FOLDER = os.path.join(PARENT_FOLDER, 'timecodes')

if not os.path.exists(TIMECODES_FOLDER):
    os.makedirs(TIMECODES_FOLDER)

FRAME_OFFSET = 1001 / 24000

def timecode_to_seconds(timecode):
    hh, mm, ss_ms = timecode.split(':')
    ss, ms = ss_ms.split('.')
    return int(hh) * 3600 + int(mm) * 60 + int(ss) + int(ms) / 1000

def seconds_to_timecode(seconds):
    td = timedelta(seconds=seconds)
    h, m, s = td.seconds // 3600, (td.seconds % 3600) // 60, td.seconds % 60
    ms = td.microseconds // 1000
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"

def get_main_sequence_id(root):
    """
    Retourne l'id XML du tractor de la séquence principale.
    C'est le tractor avec kdenlive:producer_type=17 dont l'id n'est pas un UUID
    (les sous-séquences ont des ids UUID entre accolades).
    """
    for tractor in root.findall(".//tractor"):
        t_id = tractor.get("id")
        if not t_id or t_id.startswith('{'):
            continue
        prod_type = tractor.find("./property[@name='kdenlive:producer_type']")
        if prod_type is not None and prod_type.text == '17':
            return t_id
    return None

def get_playlist_ids_for_tractor(root, tractor_id):
    """Retourne tous les ids de playlist appartenant (via sous-tractors) à un tractor."""
    tractor = root.find(f".//tractor[@id='{tractor_id}']")
    if tractor is None:
        return set()
    result = set()
    for track in tractor.findall("track"):
        ref = track.get("producer")
        if not ref:
            continue
        sub_tractor = root.find(f".//tractor[@id='{ref}']")
        if sub_tractor is not None:
            for sub_track in sub_tractor.findall("track"):
                pl_id = sub_track.get("producer")
                if pl_id:
                    result.add(pl_id)
        else:
            result.add(ref)
    return result

def build_sequence_offsets(root, main_sequence_id):
    """
    Parcourt les playlists appartenant à la séquence principale et retourne
    un dict { sequence_uuid: [offset1, offset2, ...] }.
    """
    main_playlist_ids = get_playlist_ids_for_tractor(root, main_sequence_id)
    offsets = {}

    for pl_id in main_playlist_ids:
        playlist = root.find(f".//playlist[@id='{pl_id}']")
        if playlist is None:
            continue

        timeline_position = 0.0
        clip_count = 0

        for element in playlist:
            if element.tag == "blank":
                timeline_position += timecode_to_seconds(element.get("length"))
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
                timeline_start = timeline_position + FRAME_OFFSET * clip_count

                if producer and producer.startswith('{'):
                    if producer not in offsets:
                        offsets[producer] = []
                    offsets[producer].append(timeline_start)

                timeline_position += clip_duration

    return offsets

def process_kdenlive_file(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Identifier la séquence principale et les offsets des sous-séquences
    main_sequence_id = get_main_sequence_id(root)
    sequence_offsets = build_sequence_offsets(root, main_sequence_id) if main_sequence_id else {}

    # Map playlist_id -> uuid de la séquence parente (sous-séquences uniquement)
    playlist_to_parent_sequence = {}
    for tractor in root.findall(".//tractor"):
        t_id = tractor.get("id")
        if not (t_id and t_id.startswith('{')):
            continue
        prod_type = tractor.find("./property[@name='kdenlive:producer_type']")
        if prod_type is None or prod_type.text != '17':
            continue
        for pl_id in get_playlist_ids_for_tractor(root, t_id):
            playlist_to_parent_sequence[pl_id] = t_id

    # Collecter les sources audio "video synced"
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

        pl_id = playlist.get("id")

        # Déterminer l'offset si cette playlist appartient à une sous-séquence
        parent_seq_uuid = playlist_to_parent_sequence.get(pl_id)
        if parent_seq_uuid is not None:
            parent_offsets = sequence_offsets.get(parent_seq_uuid, [])
            sequence_timeline_offset = parent_offsets[0] if parent_offsets else 0.0
        else:
            sequence_timeline_offset = 0.0

        timeline_position = 0.0
        clip_count = 0

        for element in playlist:
            if element.tag == "blank":
                timeline_position += timecode_to_seconds(element.get("length"))
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
                timeline_start = sequence_timeline_offset + timeline_position + FRAME_OFFSET * clip_count
                timeline_end = timeline_start + clip_duration

                has_asubcut = (
                    producer in video_synced_sources and
                    any(
                        filt.find("./property[@name='mlt_service']") is not None and
                        filt.find("./property[@name='mlt_service']").text == "avfilter.asubcut"
                        for filt in element.findall("filter")
                    )
                )

                has_asubboost = any(
                    filt.find("./property[@name='mlt_service']") is not None and
                    filt.find("./property[@name='mlt_service']").text == "avfilter.asubboost"
                    for filt in element.findall("filter")
                )

                if not has_asubcut and producer in video_synced_sources:
                    audio_source = video_synced_sources[producer]
                    grouped_results[audio_source].append({
                        'timeline_start': timeline_start,
                        'timeline_end': timeline_end,
                        'source_in': clip_in,
                        'source_out': clip_out,
                        'forced_sync': 'Yes' if has_asubboost else ''
                    })

                timeline_position += clip_duration

    return grouped_results

def main():
    if os.path.isdir(KDENLIVE_FOLDER):
        files = (
            glob.glob(os.path.join(KDENLIVE_FOLDER, "*.kdenlive")) +
            glob.glob(os.path.join(KDENLIVE_FOLDER, "*.xml"))
        )

        for file_path in files:
            kdenlive_name = os.path.splitext(os.path.basename(file_path))[0]
            output_subfolder = os.path.join(TIMECODES_FOLDER, kdenlive_name)
            os.makedirs(output_subfolder, exist_ok=True)

            file_results = process_kdenlive_file(file_path)
            for audio_source, clips in file_results.items():
                if not clips:
                    continue

                sorted_clips = sorted(clips, key=lambda clip: clip['timeline_start'])
                output_lines = [
                    f"{'Timeline Start':<16} {'Timeline End':<16} "
                    f"{'Source Start':<16} {'Source End':<16} {'Forced sync':<10}"
                ]

                for clip in sorted_clips:
                    line = (
                        f"{seconds_to_timecode(clip['timeline_start']):<16} "
                        f"{seconds_to_timecode(clip['timeline_end']):<16} "
                        f"{seconds_to_timecode(clip['source_in']):<16} "
                        f"{seconds_to_timecode(clip['source_out']):<16} "
                        f"{clip.get('forced_sync', ''):<10}"
                    )
                    output_lines.append(line)

                output_file = os.path.join(output_subfolder, f"{audio_source}.txt")
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write("\n".join(output_lines))
                print(f"Timecodes pour '{audio_source}' enregistrés dans : {output_file}")
    else:
        print("Le dossier 'kdenlive' n'existe pas dans le dossier parent.")

if __name__ == "__main__":
    main()