

<img width="1200" height="366" alt="DBZRBANNERCC3" src="https://github.com/user-attachments/assets/14b9a0e8-d7b3-4e7e-942e-7e9639103ce4" />



## What is it ?

These scripts allow synchronizing `.ass` subtitles synced to Dragon Box (or other editions with similar synchronization) to the Recut edition of DBZ, which is an abridged version available [here](https://nyaa.si/view/2024827).

Note that it only works with  `.ass` file format.

## Requirements

1. **Install [Python 3](https://www.python.org/downloads/) and check the "Add Python.exe to PATH."** box when installing (if you installed it without checking this box, either look on the internet how to add it to windows PATH manually, or reinstall it)
2. Then, install `ass` python module (only required to merge subtitles at the end) with this command through Windows cmd.exe or Powershell - not inside Python shell: **`pip install ass`**

## How to use it?

1. **Place the Kdenlive project files** (`.kdenlive` extension) in the **kdenlive** folder.

2. **Run the script** `1-Extract_timecodes.py`—this will create a `timecodes` folder containing `.txt` files, which will be needed for the next step.

3. **Place all your .ass subtitle files** that you want to sync in the `subtitles` folder. The script supports batch processing — you can add individual .ass files directly in the root of the folder, as well as multiple subfolders containing .ass files (for example, if you want to sync subtitles in different languages).
   
4. Run the script `2-Sync_subtitles.py`. A folder named `synced` will be created, and the synchronized subtitles (unmerged) will be saved there.  
   - **Important:** For this script to work, the ass subtitles located in the `subtitles` folder and the `.txt` files in the `timecodes` folder must share the same numbering format (nn or nnn). Example:  
     `DBZ 185 - Fuji - R2J DVD video synced - Team Mirolo.txt` and `DBZ185DVD.ass` would match.
Avoid filenames containing numbers other than the episode numbers to prevent issues from occurring.

5. **Finally, run the script** `3-Merge_subtitles_for_DBZ_Recut.py`, which uses `subdigest.py` to merge the subtitles from the `synced` folder into subtitles matching the episodes DBZ Recut edition. A folder named `subtitles for DBZ Recut` will be created, containing the final subtitles.

## Important Notes ⚠

- The `Sync_subtitles` script will automatically remove unused subtitle lines from the raw subtitles. Since it's hard to code accurate rules to delete all useless lines because it can be risky and includes lines that should be kept, there's a possibiity that you'll find an extra unused line here and there. However, after knowing this, we edited the timeline of all project files to prevent this from happening. The only way some unused line can still be present is if your subtitles display lines _way before_ a character starts speaking, or _way after_ he ends speaking, so it shouldn't happen, but it's good to know just in case.

- Also, there're some lines that you have to manually edit, because we edited the voice clip to remove a part of it, therefore the subtitle must be adapted accordingly. You can find all lines to edit [here](https://docs.google.com/spreadsheets/d/1pw--Lhc-u3Rt4GSl_2UvieFWkNJ26srMeyL7d5OQ_XM/edit?usp=sharing)

- Another thing to know is that some lines can overlap each other. It's mostly due to the audio edits mentioned previously, so it will affect very few subtitle lines. You just have to retime those lines so that they don't overlap (you can do it in softwares like Aegisub or SubtitleEdit, or even with any text editor)

## Technical Details
- For the `1-Extract_timecodes.py` script to function properly, the **audio tracks in the project must contain the phrase** `"video synced"` in their name (this is found in the `<property name="resource">` section of the `.kdenlive` file).
This is a way I found to ensure the script calculates timecodes only for broadcast audio tracks (which have names ending by "video synced") while ignoring extra timeline clips (which are unnecessary for subtitle resynchronization and may disrupt proper synchronization).
Kdenlive does not store timeline clips timecodes in it"s project files, so I had to recalculate them using the available project data:  
  - The **duration** of each track
  - Their **associated playlist (Track)**
  - The **duration of empty spaces (blank length)** between clips
  However, when calculated this way, the timecodes were **slightly off**. After analysis,, it appears that each new clip on the timeline loses approximately one video frame (~42ms).
  **Workaround:** To compensate, each clip's placement timecode is shifted +42ms per clip position (e.g., +42ms at position 1, +84ms at position 2, etc.).
  This adjustment results in **fairly accurate** timecodes. Some subtitles may still be off by **one or two video frames**, but overall synchronization remains good. If frame-perfect synchronization isn't required, the result is excellent. (PS: If you really want your subtitle lines to end along with the keyframe and not bleed into the next frame, you can use [this](https://github.com/andiandi13/SushiFix) script I made.)

- If a clip is disabled in kdenlive, subtitles of this clip - if it contains a voice - will still be generated. We've actually used this techique to generate subtitles lines for AI isolated vocals, that we aligned with a disabled audio clip containing the same voice so that it syncs the associated subtitle line.


- Compatibility of the script with other projects

These scripts are not made specifically for Dragon Ball Z serie. Actually, they can be compatible with any project made with kdenlive, but you will have to edit scripts so that they don't look for audio files named "video synced" (unless you rename your audio track like that) and change output filenames in the merging script at the end.

#### Asubcut feature

- I coded something in the script to prevent it from generating subtitle lines that aren’t used in the project (the issue I mentioned earlier).
First, you need to understand how it happens. Imagine a timeline with video and audio clips. It's cut at multiple edit points, creating many smaller clips. The issue is that sometimes, a subtitle line starts near the end of an audio clip—because just after that clip (i.e., if it hadn't been cut), there's a voice.
But since the subtitle line’s start time is often set before the voice actually plays, the line may end up being included in the audio clip we use.
So, the feature I added to the script is: if an audio clip has an effect named “Asubcut” (which is a native Kdenlive audio effect—I chose it solely because it’s a mnemonic: "A sub(title) cut"), then any subtitle lines included in that audio clip will be discarded by the script.
What we should do is: split the audio track at the end, add the “Asubcut” effect to the final clip, and disable the effect (since we don’t actually use it—it just acts as a cue for the script). Then, save the Kdenlive project and run the script on it. That's what we did for the project files of DBZ Recut so that you can synchronize your own subtitles without extra unused lines.

<img width="855" height="488" alt="2025-08-02_23_37_11-046____708x480_23 98fps_-_Kdenlive" src="https://github.com/user-attachments/assets/55528b94-1068-458a-b803-03838c50ce53" />

#### Asubboost feature
- Also, I added another feature that allows you to generate subtitles for duplicated voice clips in the timeline. By default, the script doesn't duplicate subtitles lines if clips are duplicated (for safety reason, it could generate unwanted lines). But if you want to force syncing a particular line (let's say you create some kind of flashback and re-use a voice clip from somewhere else), just add “Asubboost” effect to that clip and the script will generate it.
