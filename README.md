

<img width="1200" height="366" alt="DBZRBANNERCC3" src="https://github.com/user-attachments/assets/14b9a0e8-d7b3-4e7e-942e-7e9639103ce4" />



## What is it ?

This script allow synchronizing `.ass` subtitles synced to Dragon Box (or other editions with similar synchronization) to the Recut edition of DBZ, which is an abridged version available [here](https://nyaa.si/view/2024827).

Note that it only works with  `.ass` file format.

## Requirements

1. **Install [Python 3](https://www.python.org/downloads/) and check the "Add Python.exe to PATH."** box when installing (if you installed it without checking this box, either look on the internet how to add it to windows PATH manually, or reinstall it)
2. Then, install `ass` python module (only required to merge subtitles at the end) with this command through Windows cmd.exe or Powershell - not inside Python shell: **`pip install ass`**

## How to use it?

1. **Place the Kdenlive project files** (`.kdenlive` extension) in the **kdenlive** folder.

2. **Place all your .ass subtitle files** that you want to sync in the `subtitles` folder. The script supports batch processing, you can add individual .ass files directly in the root of the folder, as well as multiple subfolders containing .ass files (for example, if you want to sync subtitles in different languages).

3.  **Run the script** `Resync subtitles.py`— this will create multiple folders, namely `timecodes`, `synced` and `subtitles for DBZ Recut`. Only the latter matters, this is where you will find your resynced subtitles when the at the end of the process.

That's it.
   
   - **Important:** For this script to work, the ass subtitles located in the `subtitles` folder and the `.txt` files in the `timecodes` folder must share the same numbering format (nn or nnn). Since the timecodes fles are automatically named after the broadcast audio tracks, you just have to make sure that your subtitle files are named correctly, for example :
     `DBZ 185 - Fuji - R2J DVD video synced - Team Mirolo.txt` and `DBZ185DVD.ass` would match.
Avoid filenames containing numbers other than the episode numbers to prevent issues from occurring.

<details>

<summary>Important Notes</summary>

- The script automatically removes unused lines from the raw subtitles. However, since there can't be a perfect rule to delete all useless lines without risking the removal of lines that should be kept, there’s a possibility you’ll find an extra unused line here and there. We edited the timeline of all project files to prevent this as much as possible, but it’s good to know just in case you come across it.

- Also, not directly related to the script but there are some lines that you have to manually edit, because we edited the voice clip to remove a part of it, therefore the subtitle must be adapted accordingly. You can find all lines to edit [here](https://docs.google.com/spreadsheets/d/1pw--Lhc-u3Rt4GSl_2UvieFWkNJ26srMeyL7d5OQ_XM/edit?gid=1686722232#gid=1686722232)

- Another thing to know is that some lines can overlap each other. It's mostly due to the audio edits mentioned previously, so it will affect very few subtitle lines. You just have to retime those lines so that they don't overlap (you can do it in softwares like Aegisub or SubtitleEdit, or even with any text editor)

</details>

<details>
<summary>Technical Details</summary>

#### How does the script work?

The script analyzes the project files and looks for all tracks containing the words "video synced" in their filenames (this is found in the `<property name="resource">` section of the `.kdenlive` file)
This is a way I found to ensure that the script calculates timecodes only for broadcast audio tracks (which have names ending in "video synced") while ignoring other timeline clips (which are unnecessary for subtitle resynchronization and may disrupt proper synchronization).

Once those clips are identified, the script will calculate the difference between their original timestamps, and their timestamps on the Kdenlive timeline, in order to shift each and every subtitle line according to its time difference.
However, since Kdenlive does not store timeline clips timecodes in its project files, I had to recalculate them using the available project data:  
  - The **duration** of each track
  - Their **associated playlist (Track)**
  - The **duration of empty spaces (blank length)** between clips
  However, when calculated this way, the timecodes were **slightly off**. After analysis,, it appears that each new clip on the timeline loses approximately one video frame (~42ms).
  **Workaround:** To compensate, each clip's placement timecode is shifted +42ms per clip position (e.g., +42ms at position 1, +84ms at position 2, etc.).
  This adjustment results in **pretty accurate** timecodes. Some subtitles may still be off by **one or two video frames**, but overall synchronization remains good. If frame-perfect synchronization isn't required, the result is excellent. 

#### What if a timeline clip is disabled?

If a clip is disabled in kdenlive, subtitles for this clip will still be generated. We've actually used this technique to generate subtitle lines for isolated vocals (a random .wav file which does not have "video synced" in its name), that we aligned with a disabled audio clip containing the same voice so that it syncs the associated subtitle line :

<img width="500" height="474" alt="DBZR026" src="https://github.com/user-attachments/assets/c64ec0c0-33de-488f-a35f-7075928355d5" />

#### Subtitle exclusion : Asubcut (audio) / nosync0r (video)

Sometimes, a subtitle line starts near the end of an audio clip, because just after that clip (i.e., if it hadn't been cut), there's a voice. Since the subtitle line's start time is often set before the voice actually plays, the line may end up being incorrectly included in the preceding clip.
To prevent this, split the clip just before the point where that unwanted line would be generated, then add the Asubcut effect (on audio clips) or nosync0r (on video clips) to the final clip, and disable the effect (since it's not actually used for its intended purpose, but just acts as a cue for the script). Any subtitle lines included in that marked clip will then be discarded.

"Asubcut" and "nosync0r" were just chosen as mnemonics: "A subtitle cut" and "No synchronization"

<img width="855" height="488" alt="..." src="https://github.com/user-attachments/assets/55528b94-1068-458a-b803-03838c50ce53" />

#### Force subtitle duplication : Asubboost (audio) / Fsync (video)

By default, the script won't generate subtitle lines for duplicated clips (as a safety measure against unwanted duplicates). If you intentionally reuse a voice clip, for instance in a flashback, add the Asubboost effect (on audio clips) or Fsync (on video clips) to that clip to force subtitle generation for it.

"Asubboost" and "Fsync" were also chosen as mnemonics: "A subtitle boost" and "Force synchronization"

#### Compatibility of the script with other projects

This script is not made specifically for Dragon Ball Z Recut. Actually, it can be compatible with any project made with kdenlive, but you will have to either : 
- Edit the script "Extract_timecodes.py" located in _dependencies folder, so that it doesn't look for audio files named "video synced", and replace that by another phrase unique to your own filenames
- Or, rename your video or audio tracks and include "video synced" in their filenames

</details>
