# Music and Memory Task

Static page, no install. Open `index.html` in Chrome or Edge, or host the folder (GitHub Pages, any shared drive web server). Audio autoplay needs a click first, and the page always has one.

## Stimuli
Raga Shankarabharanam (S R2 G3 M1 P D2 N3: exactly the Western major scale; Bilawal in Hindustani music), Adi talam, Sa = Eb. Built from real recorded samples by `make_stimuli.py`:

| File | Condition |
|---|---|
| `A_raga_slow.mp3` | Indian style: solo violin with continuous gamakas (Ga long and plain, Ni light, kampita on Ri/Ma/Dha, descending notes approached from above, sphuritam on repeated notes), just intonation, Sa/Pa steady; real tanpura; real mridangam (moras into samam); 60 BPM |
| `B_raga_fast.mp3` | Same at 120 BPM |
| `C_western_slow.mp3` | Western style: the same violin samples and melody, equal temperament, one bow per note, no slides; piano broken chords and cello with major-key harmony (I ii iii IV V vi) fitted to the melody, soft drum kit; 60 BPM |
| `D_western_fast.mp3` | Same as C at 120 BPM |

Quiet (E) is silence. The piece has 32 avartanams: pallavi with four sangatis, anupallavi, pallavi, kalpanaswaram-style passages ending in a mora, charanam, pallavi, ending. Files are 256 s, loop seamlessly and are RMS-matched. `midi/shankarabharanam_notation.txt` has the composition in swara notation for a Carnatic musician to review; `midi/*.mid` has the plain melody and the Western backing.

Samples (all real recordings):
- Violin: VSCO 2 Community Edition, solo violin Arco Vib p (CC0), github.com/sgossner/VSCO-2-CE (SFZ branch).
- Mridangam: IITM-CompMusic Mridangam Stroke Dataset, D# tonic, Freesound pack 14163 by akshaylaya (CC BY-NC 3.0). Anantapadmanabhan, Bellur & Murthy (2013), ICASSP, 181–185, doi:10.1109/ICASSP.2013.6637633.
- Tanpura: "Tambura_Eb_fat" by Kaczinski, Freesound 506312 (CC0).
- Western backing: GeneralUser GS soundfont (free licence) via FluidSynth.

To regenerate (needs numpy, mido, soundfile; put the samples in `ASSETS/violin`, `ASSETS/mridangam`, `ASSETS/tanpura_Eb.mp3`):
```
python make_stimuli.py --assets ASSETS --fluidsynth PATH/fluidsynth.exe --gm PATH/GeneralUser-GS.sf2
```

## Flow
1. Start screen (roll number, required; Carnatic and Hindustani familiarity, training, hearing check). Roll numbers link a student's sessions and must be removed before data are shared. Works on phones and computers: answers are entered on an on-screen keypad (1–9, –, ⌫, Done) or a physical keyboard; the device (`device`: touch/computer) and input method per list (`input`: keypad/keyboard) are recorded. On the Begin tap all tracks are unlocked for iPhone playback, and the screen is kept awake (Wake Lock) during the session. Phones and tablets are told to use a laptop (typing digits needs a keyboard).
2. Order assignment: one of 10 Williams-design orders of the 5 conditions (each condition appears in each position twice and directly follows every other condition twice). Taken in rotation from DataPipe's condition counter when it is switched on (set it to 10 conditions); otherwise random. Recorded as `order_row`, `order`, `order_source`.
3. Volume check with a music sample. All four tracks start downloading here; each block waits until its track can play through.
4. Practice without music: 2 serial-recall lists with feedback, then one baseline "right now" alertness and mood rating (logged as block 0, condition `baseline`).
5. Five blocks. Each block: 30 s listening → "Numbers" cue → **serial recall**, 8 lists of 9 digits (all of 1–9 in random order, no runs like 3-4-5; 0.75 s on, 0.25 s off; "List k of 8" shown; type them back in order, `-` for forgotten ones, all 9 positions required, no time limit) → ratings, every point labelled ("during this block" alertness and mood, and "how Indian" for music blocks) → 20 s rest ending with a soft chime. Music plays from the start of the block through the lists.
6. Results table and upload.

About 18 minutes in total. Leaving the page mid-session triggers a "leave site?" prompt; switching tabs during a block shows a warning on return and is recorded (`tab_hidden_count`, and `tab_hidden_so_far` per list).

## URL options
- `?fast=1` shortens lead-in and rest (3 s and 2 s) for piloting.
- `?row=3` forces order 1–10 (Williams design). Default: DataPipe rotation, else random.
- `?nosave=1` runs without uploading (data can still be downloaded at the end).

## Output
At the end the page uploads two CSVs to DataPipe (experiment `hmU1FxSIMrPB`), which stores them in its Google Drive folder:
- `<ID>_<session>_trials.csv`: one row per recall list (stimulus, response, correct positions, response time) and rating, with condition, block position, order, Carnatic and Hindustani familiarity and training.
- `<ID>_<session>_blocks.csv`: per-block summary (recall proportion correct in position, perfect lists, ratings, tab_hidden_count, audio_ok).

`session` is random per run, so two students typing the same ID never overwrite each other. Runs with `?fast=1` are prefixed `TEST_` and have `test_run = 1`; `?nosave=1` uploads nothing. If the upload fails, the page shows the error, a retry button and download buttons.

**Progress saving.** After every completed block the page (1) saves its state in the browser (localStorage) and (2) uploads `<ID>_<session>_progress_b<N>.csv` with all trials so far, in the background. If the tab closes or the page reloads, opening the link again on the same computer (within 6 hours) offers *Continue my session* (same order, practice not repeated; the interrupted block restarts from its beginning and its partial data is discarded) or *Start over*. A session that finished but failed to upload offers *Save my answers*. Rows record `resumes` (how many times the session was resumed). For analysis, use the final `_trials.csv` when it exists, otherwise the highest-numbered `_progress_b<N>` file for that session.

## Notes
- Williams design balances position and first-order carry-over across every 10 participants; block position is still in the data as a covariate.
- Hearing and volume are self-reported and self-set.
