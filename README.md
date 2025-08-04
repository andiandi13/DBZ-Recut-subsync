![Jartcut](https://github.com/user-attachments/assets/d9373bea-ff08-474c-a395-3f3a450cdcd5)

## What is it ?

These scripts allow synchronizing `.ass` subtitles synced to Dragon Box (or other editions with similar synchronization) to the Jartcut edition of DBZ, which is an abridged version available here: [https://nyaa.si/view/1936292](https://nyaa.si/view/1936292).

Note that it only works with  `.ass` file format.

## Requirements

1. **Install [Python 3](https://www.python.org/downloads/) and check the "Add Python.exe to PATH."** box when installing (if you installed it without checking this box, either look on the internet how to add it to windows PATH manually, or reinstall it)
2. Then, install `ass` python module (only required to merge subtitles at the end) with this command through Windows cmd.exe or Powershell - not inside Python shell:
### `pip install ass`

## How to use it?

1. **Place the Kdenlive project files** (`.kdenlive` extension) in the **kdenlive** folder.

2. **Run the script** `1-Extract_timecodes.py`—this will create a `timecodes` folder containing `.txt` files, which will be needed for the next step.

3. **Place the `.ass` subtitles files** you want to sync in the **subtitles** folder
   
4. Run the script `2-Sync_subtitles.py`. A **"synced"** folder will be created, and the synchronized subtitles (unmerged) will be saved there.  
   - **Important:** For this script to work, the ass subtitles located in the `subtitles` folder and the `.txt` files in the `timecodes` folder must share the same numbering format (nn or nnn). Example:  
     `DBZ 185 - Fuji - R2J DVD video synced - Team Mirolo.txt` and `DBZ185DVD.ass` would match.
Avoid filenames containing numbers other than the episode numbers to prevent issues from occurring.

5. **Finally, run the script** `3-Merge_subtitles_for_Jartcut.py`, which uses `subdigest.py` to merge the subtitles from the `synced` folder into subtitles matching the episodes DBZ Recut edition. A folder named `subtitles for Jartcut` will be created, containing the final subtitles.

## Important Notes ⚠

- The `Sync_subtitles` script will automatically remove unused subtitle lines from the raw subtitles. Since it's hard to code accurate rules to delete all useless lines because it can be risky and includes lines that should be kept, there's a possibiity that you'll find an extra unused line here and there. However, after knowing this, we edited the timeline of all project files to prevent this from happening. The only way some unused line can still be present is if your subtitles display lines _way_ before a character starts speaking, or _way_ before he ends speaking, so it shouldn't happen, but it's good to know just in case.

- Also, there're some lines that you have to manually edit, because we edited the voice to remove a part of it, therefore the subtitle must be adapted accordingly. You can find all lines to edit [here](https://docs.google.com/spreadsheets/d/1pw—Lhc-u3Rt4GSl_2UvieFWkNJ26srMeyL7d5OQ_XM/edit?gid=1686722232#gid=1686722232)

- Similarly, some lines can overlap each other. It's mostly - or completely, due to the audio edits mentioned previously and it will affect very few subtitle lines. You just have to retime those lines so that they don't overlap (you can do it in softwares like Aegisub or subtitles edit, or even with any text editor)

## Technical Details
- For the `1-Extract_timecodes.py` script to function properly, the **audio tracks in the project must contain the phrase** `"video synced"` in their name (this is found in the `<property name="resource">` section of the `.kdenlive` file).
This is currently the only way I found to ensure the script calculates timecodes only for broadcast audio tracks (which have names ending by "video synced") while ignoring extra timeline clips (which are unnecessary for subtitle resynchronization and may disrupt proper synchronization).

- Kdenlive does not store timeline clips timecodes in it"s project files, so I had to recalculate them using the available project data:  
  - The **duration** of each track
  - Their **associated playlist (Track)**
  - The **duration of empty spaces (blank length)** between clips
  However, when calculated this way, the timecodes were **slightly off**. After analysis,, it appears that each new clip on the timeline loses approximately one video frame (~42ms).
  **Workaround:** To compensate, each clip's placement timecode is shifted +42ms per clip position (e.g., +42ms at position 1, +84ms at position 2, etc.).
  This adjustment results in **fairly accurate** timecodes. Some subtitles may still be off by **one or two video frames**, but overall synchronization remains good. If frame-perfect synchronization isn't required, the result is excellent.

- Further compatibility of the scripts

These scripts are not made specifically for Dragon Ball Z serie. Actually, they can be compatible with any recut project made with kdenlive, but you will have to edit scripts so that they don't look for audio files named "video synced" (unless you rename your audio track like that) and change output filenames in the merging script at the end.
