# Music and Memory Task

Static page, no install. Open `index.html` in Chrome or Edge, or host the folder (GitHub Pages, any shared drive web server). Audio autoplay needs a click first, and the page always has one.

## Stimuli
Composed as MIDI in code and rendered with sampled instruments by `make_stimuli.py`:

| File | Condition |
|---|---|
| `A_raga_slow.mp3` | Flute melody with meend, kan and vibrato; tanpura drone (sitar patch); tabla teentaal with fills; 60 BPM |
| `B_raga_fast.mp3` | Same at 120 BPM |
| `C_western_slow.mp3` | Same melody on piano, no ornaments; left-hand broken chords (G, Em, Asus4, Dsus2: Bhupali pitches only), bass, drum kit; 60 BPM |
| `D_western_fast.mp3` | Same as C at 120 BPM |

Quiet (E) is silence. The piece is 16 teentaal cycles (sthayi, development, antara, tans, return), no cycle repeated. Each file is 256 s and loops seamlessly; all are RMS-matched. `midi/` has the full arrangements for editing in MuseScore or a DAW (the tabla track uses the Tabla.sf2 note map, so it sounds wrong with a General MIDI soundfont).

To regenerate (needs numpy, mido, soundfile):
```
python make_stimuli.py --fluidsynth PATH/fluidsynth.exe --gm PATH/GeneralUser-GS.sf2 --tabla PATH/Tabla.sf2
```
FluidSynth: github.com/FluidSynth/fluidsynth releases. GeneralUser GS: github.com/mrbumpy409/GeneralUser-GS (free licence). Tabla.sf2: CPAN module Music::Percussion::Tabla (Artistic License 2.0).

## Flow
Consent and info, volume check, one practice of each task (no music), then 5 blocks in the student's Latin-square order: 1 min listening, backward digit span, 24-trial Stroop (music still playing), two ratings, 20 s rest. About 25 min.

## URL options
- `?fast=1` shortens lead-in and rest (3 s and 2 s) for piloting.
- `?row=3` forces Latin-square row 1–5. Default is random.

## Output
Students download two CSVs at the end:
- `trials_<ID>.csv`: one row per digit list, Stroop trial and rating (RT in ms, condition, block position, familiarity, training).
- `blocks_<ID>.csv`: per-block summary (max span, total, Stroop interference, error rate, ratings).

Progress is also backed up in the browser's localStorage after every trial.

## Notes
- Stroop RT is measured with `performance.now()` from the frame after the word is drawn. Fine for class-level differences, not a lab-grade timer.
- Cyclic Latin square does not balance carry-over; block position is in the data so it can be used as a covariate.
- Hearing and volume are self-reported and self-set.
