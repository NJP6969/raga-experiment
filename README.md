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
1. Start screen (ID, Carnatic and Hindustani familiarity, training, hearing check). Phones and tablets are told to use a laptop (the colour task needs a keyboard).
2. Volume check with a music sample. All four tracks start downloading here; each block waits until its track can play through.
3. Practice without music: 2 serial-recall lists (with feedback) and 8 Stroop trials (with feedback).
4. Five blocks in the student's Latin-square order. Each block: 1 min listening → "Numbers" cue → **serial recall**, 6 lists of 8 digits (8 of the digits 1–9, no repeats, no runs like 3-4-5; 0.75 s on, 0.25 s off; type them back in order, `-` for forgotten ones, all 8 positions required) → "Colours" cue → **Stroop**, 48 trials (24 congruent, 24 incongruent; no identical back-to-back trials, no ink three times running; 2 s response limit) → ratings (alertness, mood, and "how Indian" for music blocks) → 20 s rest. Music plays from the start of the block through both tasks.
5. Results table and upload.

About 24 minutes in total. Leaving the page mid-session triggers a "leave site?" prompt; how often the tab was hidden during each block is recorded (`tab_hidden_count`).

## URL options
- `?fast=1` shortens lead-in and rest (3 s and 2 s) for piloting.
- `?row=3` forces Latin-square row 1–5. Default is random.
- `?nosave=1` runs without uploading (data can still be downloaded at the end).

## Output
At the end the page uploads two CSVs to DataPipe (experiment `hmU1FxSIMrPB`), which stores them in its Google Drive folder:
- `<ID>_<session>_trials.csv`: one row per recall list (stimulus, response, correct positions), Stroop trial (word, ink, response, RT in ms) and rating, with condition, block position, Carnatic and Hindustani familiarity and training.
- `<ID>_<session>_blocks.csv`: per-block summary (recall proportion correct in position, perfect lists, Stroop congruent/incongruent RT, interference, error rate, ratings, tab_hidden_count, audio_ok).

`session` is random per run, so two students typing the same ID never overwrite each other. Runs with `?fast=1` are prefixed `TEST_` and have `test_run = 1`; `?nosave=1` uploads nothing. If the upload fails, the page shows the error, a retry button and download buttons. Progress is also backed up in the browser's localStorage after every trial.

## Notes
- Stroop RT is measured with `performance.now()` from the frame after the word is drawn. Fine for class-level differences, not a lab-grade timer.
- Cyclic Latin square does not balance carry-over; block position is in the data so it can be used as a covariate.
- Hearing and volume are self-reported and self-set.
