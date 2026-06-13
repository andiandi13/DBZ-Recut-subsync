import subprocess
import os
from datetime import datetime

# Folder containing the dependency scripts
DEPENDENCY_FOLDER = os.path.join(os.getcwd(), "_dependencies")

# Logs folder inside _dependencies (created automatically if missing)
LOGS_FOLDER = os.path.join(DEPENDENCY_FOLDER, "logs")
os.makedirs(LOGS_FOLDER, exist_ok=True)

# Scripts to run in order
scripts = [
    "Extract_timecodes.py",
    "Sync_subtitles.py",
    "Merge_subtitles_for_DBZ_Recut.py"
]

# Create a timestamp for the log file: YYYY-MM-DD-HH-MM-SS.ms
# Replacing : by - for Windows compatibility
timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S.%f")[:-3]
log_file_path = os.path.join(LOGS_FOLDER, f"log-{timestamp}.txt")

def timestamped_line(line):
    """Prefix a log line with current time [HH:MM:SS]"""
    now = datetime.now().strftime("[%H:%M:%S]")
    return f"{now} {line}\n"

def run_script(script_name):
    script_path = os.path.join(DEPENDENCY_FOLDER, script_name)
    if not os.path.isfile(script_path):
        print(f"Script not found: {script_path}")
        return False

    print(timestamped_line(f"Running {script_name}..."), end="")
    with open(log_file_path, "a", encoding="utf-8") as log_file:
        log_file.write(timestamped_line(f"--- Running {script_name} ---"))
        log_file.flush()
        try:
            subprocess.run(
                ["python", script_name],
                stdout=log_file,
                stderr=log_file,
                cwd=DEPENDENCY_FOLDER,
                check=True
            )
            log_file.write(timestamped_line(f"--- {script_name} completed successfully ---"))
            print(timestamped_line(f"{script_name} completed successfully."), end="")
            return True
        except subprocess.CalledProcessError:
            log_file.write(timestamped_line(f"--- {script_name} failed ---"))
            print(timestamped_line(f"Error: {script_name} failed. Check {log_file_path} for details."), end="")
            return False

def main():
    start_time = datetime.now()
    print(timestamped_line(f"Execution log will be saved to: {log_file_path}"), end="")
    with open(log_file_path, "a", encoding="utf-8") as log_file:
        log_file.write(timestamped_line("Execution started\n"))

    for script in scripts:
        success = run_script(script)
        if not success:
            print(timestamped_line("Stopping execution due to error."), end="")
            break

    end_time = datetime.now()
    duration = end_time - start_time
    duration_str = str(duration).split(".")[0]  # H:M:S
    print(timestamped_line(f"Total execution time: {duration_str}"), end="")
    with open(log_file_path, "a", encoding="utf-8") as log_file:
        log_file.write(timestamped_line(f"Total execution time: {duration_str}"))

if __name__ == "__main__":
    main()