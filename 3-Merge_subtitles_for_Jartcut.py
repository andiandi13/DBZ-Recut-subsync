import os
import re
import subprocess

# Dossier contenant les fichiers .ass
input_directory = 'synced'  # Assurez-vous que ce dossier existe
output_directory = 'subtitles for Jartcut'  # Dossier de sortie

# Vérifier et créer le dossier de sortie si nécessaire
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# Plan de fusion, spécifiant les groupes de fichiers à fusionner
merging_plan = {
    "Dragon Ball Z Jartcut 001.ass": ["001", "002"],
    "Dragon Ball Z Jartcut 002.ass": ["003"],
    "Dragon Ball Z Jartcut 003.ass": ["004"],
    "Dragon Ball Z Jartcut 004.ass": ["005"],
    "Dragon Ball Z Jartcut 005.ass": ["006"],
    "Dragon Ball Z Jartcut 006.ass": ["007", "008"],
    "Dragon Ball Z Jartcut 007.ass": ["011", "017", "018", "014"],
    "Dragon Ball Z Jartcut 008.ass": ["019", "020"],
    "Dragon Ball Z Jartcut 009.ass": ["021"],
    "Dragon Ball Z Jartcut 010.ass": ["022"],
    "Dragon Ball Z Jartcut 011.ass": ["023", "024"],
    "Dragon Ball Z Jartcut 012.ass": ["025", "026"],
    "Dragon Ball Z Jartcut 013.ass": ["027", "028"],
    "Dragon Ball Z Jartcut 014.ass": ["029"],
    "Dragon Ball Z Jartcut 015.ass": ["030"],
    "Dragon Ball Z Jartcut 016.ass": ["031", "032"],
    "Dragon Ball Z Jartcut 017.ass": ["033"],
    "Dragon Ball Z Jartcut 018.ass": ["034"],
    "Dragon Ball Z Jartcut 019.ass": ["035"],
    "Dragon Ball Z Jartcut 020.ass": ["036"],
    "Dragon Ball Z Jartcut 021.ass": ["037"],
    "Dragon Ball Z Jartcut 022.ass": ["038", "039", "040", "042", "043"],
    "Dragon Ball Z Jartcut 023.ass": ["044", "045"],
    "Dragon Ball Z Jartcut 024.ass": ["046"],
    "Dragon Ball Z Jartcut 025.ass": ["047"],
    "Dragon Ball Z Jartcut 026.ass": ["048"],
    "Dragon Ball Z Jartcut 027.ass": ["049", "050"],
    "Dragon Ball Z Jartcut 028.ass": ["051"],
    "Dragon Ball Z Jartcut 029.ass": ["052", "053"],
    "Dragon Ball Z Jartcut 030.ass": ["054"],
    "Dragon Ball Z Jartcut 031.ass": ["055", "056", "057"],
    "Dragon Ball Z Jartcut 032.ass": ["058"],
    "Dragon Ball Z Jartcut 033.ass": ["059", "060", "061"],
    "Dragon Ball Z Jartcut 034.ass": ["062"],
    "Dragon Ball Z Jartcut 035.ass": ["063", "064"],
    "Dragon Ball Z Jartcut 036.ass": ["065", "066"],
    "Dragon Ball Z Jartcut 037.ass": ["067", "068"],
    "Dragon Ball Z Jartcut 038.ass": ["069", "070"],
    "Dragon Ball Z Jartcut 039.ass": ["071", "072"],
    "Dragon Ball Z Jartcut 040.ass": ["073", "074"],
    "Dragon Ball Z Jartcut 041.ass": ["075", "076"],
    "Dragon Ball Z Jartcut 042.ass": ["077", "078"],
    "Dragon Ball Z Jartcut 043.ass": ["079", "080"],
    "Dragon Ball Z Jartcut 044.ass": ["081", "082"],
    "Dragon Ball Z Jartcut 045.ass": ["083"],
    "Dragon Ball Z Jartcut 046.ass": ["084", "085"],
    "Dragon Ball Z Jartcut 047.ass": ["086"],
    "Dragon Ball Z Jartcut 048.ass": ["087", "088"],
    "Dragon Ball Z Jartcut 049.ass": ["089", "090", "091"],
    "Dragon Ball Z Jartcut 050.ass": ["092", "093", "094", "095"],
    "Dragon Ball Z Jartcut 051.ass": ["096", "097"],
    "Dragon Ball Z Jartcut 052.ass": ["098", "099"],
    "Dragon Ball Z Jartcut 053.ass": ["100", "101", "103"],
    "Dragon Ball Z Jartcut 054.ass": ["104", "105"],
    "Dragon Ball Z Jartcut 055.ass": ["106", "107"],
    "Dragon Ball Z Jartcut 056.ass": ["118", "119"],
    "Dragon Ball Z Jartcut 057.ass": ["120"],
    "Dragon Ball Z Jartcut 058.ass": ["121"],
    "Dragon Ball Z Jartcut 059.ass": ["122"],
    "Dragon Ball Z Jartcut 060.ass": ["123"],
    "Dragon Ball Z Jartcut 061.ass": ["125", "126"],
    "Dragon Ball Z Jartcut 062.ass": ["127"],
    "Dragon Ball Z Jartcut 063.ass": ["128", "129"],
    "Dragon Ball Z Jartcut 064.ass": ["130"],
    "Dragon Ball Z Jartcut 065.ass": ["131", "132"],
    "Dragon Ball Z Jartcut 066.ass": ["133", "134"],
    "Dragon Ball Z Jartcut 067.ass": ["135", "136"],
    "Dragon Ball Z Jartcut 068.ass": ["137", "138"],
    "Dragon Ball Z Jartcut 069.ass": ["139", "140"],
    "Dragon Ball Z Jartcut 070.ass": ["141"],
    "Dragon Ball Z Jartcut 071.ass": ["142"],
    "Dragon Ball Z Jartcut 072.ass": ["143", "144"],
    "Dragon Ball Z Jartcut 073.ass": ["145", "146"],
    "Dragon Ball Z Jartcut 074.ass": ["147", "148", "149"],
    "Dragon Ball Z Jartcut 075.ass": ["150", "151"],
    "Dragon Ball Z Jartcut 076.ass": ["152"],
    "Dragon Ball Z Jartcut 077.ass": ["153", "154"],
    "Dragon Ball Z Jartcut 078.ass": ["155", "156"],
    "Dragon Ball Z Jartcut 079.ass": ["157", "158", "159"],
    "Dragon Ball Z Jartcut 080.ass": ["160", "161"],
    "Dragon Ball Z Jartcut 081.ass": ["162", "163", "164", "165"],
    "Dragon Ball Z Jartcut 082.ass": ["166", "167"],
    "Dragon Ball Z Jartcut 083.ass": ["168", "169"],
    "Dragon Ball Z Jartcut 084.ass": ["172", "173"],
    "Dragon Ball Z Jartcut 085.ass": ["174", "176", "175"],
    "Dragon Ball Z Jartcut 086.ass": ["177", "178", "179"],
    "Dragon Ball Z Jartcut 087.ass": ["180", "181", "182"],
    "Dragon Ball Z Jartcut 088.ass": ["183", "184"],
    "Dragon Ball Z Jartcut 089.ass": ["185", "186", "187"],
    "Dragon Ball Z Jartcut 090.ass": ["188", "189"],
    "Dragon Ball Z Jartcut 091.ass": ["190", "191"],
    "Dragon Ball Z Jartcut 092.ass": ["192"],
    "Dragon Ball Z Jartcut 093.ass": ["193"],
    "Dragon Ball Z Jartcut 094.ass": ["194"],
    "Dragon Ball Z Jartcut 095.ass": ["200"],
    "Dragon Ball Z Jartcut 096.ass": ["201"],
    "Dragon Ball Z Jartcut 097.ass": ["204", "205", "206"],
    "Dragon Ball Z Jartcut 098.ass": ["207"],
    "Dragon Ball Z Jartcut 099.ass": ["208"],
    "Dragon Ball Z Jartcut 100.ass": ["209", "210"],
    "Dragon Ball Z Jartcut 101.ass": ["211", "212"],
    "Dragon Ball Z Jartcut 102.ass": ["213", "214"],
    "Dragon Ball Z Jartcut 103.ass": ["215", "216"],
    "Dragon Ball Z Jartcut 104.ass": ["217", "218"],
    "Dragon Ball Z Jartcut 105.ass": ["219"],
    "Dragon Ball Z Jartcut 106.ass": ["220"],
    "Dragon Ball Z Jartcut 107.ass": ["221", "222"],
    "Dragon Ball Z Jartcut 108.ass": ["223", "224", "225"],
    "Dragon Ball Z Jartcut 109.ass": ["226", "227"],
    "Dragon Ball Z Jartcut 110.ass": ["228", "229"],
    "Dragon Ball Z Jartcut 111.ass": ["230", "231", "232"],
    "Dragon Ball Z Jartcut 112.ass": ["233", "234"],
    "Dragon Ball Z Jartcut 113.ass": ["235", "236", "237"],
    "Dragon Ball Z Jartcut 114.ass": ["238", "239", "240"],
    "Dragon Ball Z Jartcut 115.ass": ["241", "242"],
    "Dragon Ball Z Jartcut 116.ass": ["243", "244"],
    "Dragon Ball Z Jartcut 117.ass": ["245", "246"],
    "Dragon Ball Z Jartcut 118.ass": ["247", "248"],
    "Dragon Ball Z Jartcut 119.ass": ["249", "250"],
    "Dragon Ball Z Jartcut 120.ass": ["251", "252"],
    "Dragon Ball Z Jartcut 121.ass": ["253", "254"],
    "Dragon Ball Z Jartcut 122.ass": ["255", "256"],
    "Dragon Ball Z Jartcut 123.ass": ["257"],
    "Dragon Ball Z Jartcut 124.ass": ["258", "259"],
    "Dragon Ball Z Jartcut 125.ass": ["260", "261"],
    "Dragon Ball Z Jartcut 126.ass": ["262", "263"],
    "Dragon Ball Z Jartcut 127.ass": ["264", "265"],
    "Dragon Ball Z Jartcut 128.ass": ["266", "267", "268"],
    "Dragon Ball Z Jartcut 129.ass": ["269", "270", "271", "272"],
    "Dragon Ball Z Jartcut 130.ass": ["273", "274", "275", "276"],
    "Dragon Ball Z Jartcut 131.ass": ["277", "278", "279"],
    "Dragon Ball Z Jartcut 132.ass": ["280", "281", "282"],
    "Dragon Ball Z Jartcut 133.ass": ["283", "284"],
    "Dragon Ball Z Jartcut 134.ass": ["285", "286"],
    "Dragon Ball Z Jartcut 135.ass": ["287"],
    "Dragon Ball Z Jartcut 136.ass": ["289", "290", "291"]
    "Dragon Ball Z Jartcut 006.5.ass": ["009", "010", "014"],
    "Dragon Ball Z Jartcut 031.5.ass": ["003"],
	"Dragon Ball Z Jartcut 055.5.ass": ["118", "119"],
	"Dragon Ball Z Jartcut 060.5.ass": ["124", "125"],
    "Dragon Ball Z Jartcut 084.5.ass": ["169", "170", "171", "172", "174"],
}

# Fonction pour extraire le numéro du fichier sans tenir compte des zéros initiaux
def extract_number_from_filename(filename):
    match = re.search(r'(\d+)(?=[^0-9]*\.ass)', filename)
    if match:
        return match.group(1).zfill(3)
    return None

# Fonction pour collecter les fichiers .ass dans le dossier
def collect_ass_files(directory):
    ass_files = []
    for filename in os.listdir(directory):
        if filename.endswith('.ass'):
            file_number = extract_number_from_filename(filename)
            if file_number:
                ass_files.append((filename, file_number))
    return ass_files

# Fonction pour fusionner les fichiers
def merge_files(merge_target, files_to_merge):
    output_path = os.path.join(output_directory, merge_target)
    # Construction de la commande :
    # Le premier fichier avec l'option -i et les suivants avec --merge-file
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
    ass_files = collect_ass_files(input_directory)
    for target_file, numbers in merging_plan.items():
        files_found = []
        for num in numbers:
            for file_name, file_number in ass_files:
                # On vérifie si le numéro demandé est contenu dans le nom complet du fichier (ex : "228" dans "DBZ_228ds.ass")
                if num in file_name:
                    full_path = os.path.join(input_directory, file_name)
                    if full_path not in files_found:
                        files_found.append(full_path)
        if files_found:
            print(f"Fusion de {files_found} dans {target_file}")
            merge_files(target_file, files_found)
        else:
            print(f"Aucun fichier trouvé pour fusionner dans {target_file}")

if __name__ == '__main__':
    main()
