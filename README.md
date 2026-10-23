# Music and Memory Task

Static page, no install. Open `index.html` in Chrome or Edge, or host the folder (GitHub Pages, any shared drive web server). Audio autoplay needs a click first, and the page always has one. Works on phones, tablets (iPad), laptops and desktops, in a light or dark theme.

The site itself is `index.html` (the task), `test.html` (stimulus check), `assets/` (shared theme colours and theme switching) and `stimuli/`. Everything else (`tests/`, `package.json`, `.github/`) is only for testing and CI/CD and is not needed to run the task.

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
1. Start screen (intro). First question: **"Are you part of the Music Course?"** Yes → full name and roll number, both required. No → only the roll number field is shown, and it is optional. A roll number, when given, must be **exactly 10 digits** (the field keeps digits only, stops at 10 and shows an error if left incomplete). Then Carnatic and Hindustani familiarity, training, hearing check. Names and roll numbers link a student's sessions and record course participation; both must be removed before data are shared. Without a roll number the session gets a unique anonymous ID `anon-<session>`, so anonymous students are never merged in the analysis. Works on phones, tablets and computers: answers are entered on an on-screen keypad (1–9, –, ⌫, Done) or a physical keyboard; the device (`device`: touch/computer) and input method per list (`input`: keypad/keyboard) are recorded. On the Begin tap all tracks are unlocked for iPhone playback, and the screen is kept awake (Wake Lock) during the session. (Earlier versions told phone and tablet users to use a laptop; since the on-screen keypad, phones and tablets are supported.)
2. Setup: **choose a theme** (System, Light or Dark). Until the participant picks, the page follows the device setting (System). The page changes as soon as an option is picked, and a preview shows a digit, the keypad and a rating scale in that theme, so participants can compare before continuing. The choice is remembered on that device (also on `test.html`) and recorded (`theme`, `theme_resolved`).
3. Order assignment: one of 10 Williams-design orders of the 5 conditions (each condition appears in each position twice and directly follows every other condition twice). Taken in rotation from DataPipe's condition counter when it is switched on (set it to 10 conditions); otherwise random. Recorded as `order_row`, `order`, `order_source`.
4. Volume check with a music sample. All four tracks start downloading here; each block waits until its track can play through.
5. Practice ("testing") without music: 2 serial-recall lists with feedback, then one baseline "right now" alertness and mood rating (logged as block 0, condition `baseline`).
6. Five blocks. Each block: 30 s listening → "Numbers" cue → **serial recall**, 8 lists of 9 digits (all of 1–9 in random order, no runs like 3-4-5; 0.75 s on, 0.25 s off; "List k of 8" shown; type them back in order, `-` for forgotten ones, all 9 positions required, no time limit) → ratings, every point labelled ("during this block" alertness and mood, and "how Indian" for music blocks) → 20 s rest ending with a soft chime. Music plays from the start of the block through the lists.
7. Results table and upload.

**Progress bar.** The bar at the top appears only on the first page of each phase, with its name and how much of the whole session is done: Intro, Setup (theme), Practice, Questions before the task (baseline rating), About the task (before the blocks and at the start of each block), Questions after each block, Finished. It is hidden on every other page (volume, lists, answers, lead-in, rests), so nothing distracts during the task. It only goes up; a resumed session continues from the progress it had reached.

**Theme and colours.** One simple palette (neutral greys with an indigo accent) in a light and a dark version, defined once in `assets/theme.css`; all text meets WCAG AA contrast in both. `assets/theme.js` applies the choice before the page draws (no flash) and follows the device live when System is chosen. The resume page also leads through the theme page, with the saved choice selected.

About 18 minutes in total. Leaving the page mid-session triggers a "leave site?" prompt; switching tabs during a block shows a warning on return and is recorded (`tab_hidden_count`, and `tab_hidden_so_far` per list).

## URL options
- `?fast=1` shortens lead-in and rest (3 s and 2 s) for piloting.
- `?row=3` forces order 1–10 (Williams design). Default: DataPipe rotation, else random.
- `?nosave=1` runs without uploading (data can still be downloaded at the end).

## Output
At the end the page uploads two CSVs to DataPipe (experiment `hmU1FxSIMrPB`), which stores them in its Google Drive folder:
- `<ID>_<session>_trials.csv`: one row per recall list (stimulus, response, correct positions, response time) and rating, with condition, block position, order, Carnatic and Hindustani familiarity and training, `music_course` (1 = yes, 0 = no), `full_name` (empty when not in the course), `theme` (system/light/dark) and `theme_resolved` (light/dark actually shown).
- `<ID>_<session>_blocks.csv`: per-block summary (recall proportion correct in position, perfect lists, ratings, tab_hidden_count, audio_ok, music_course, full_name, theme).

`<ID>` is the roll number, or `anon-<session>` for students outside the course who gave none. `full_name` and roll numbers are personal data: remove them before sharing. The analysis never copies names into its outputs, but roll numbers stay in `clean_digit_level.csv` (column `participant`).

`session` is random per run, so two students typing the same ID never overwrite each other. Runs with `?fast=1` are prefixed `TEST_` and have `test_run = 1`; `?nosave=1` uploads nothing. If the upload fails, the page shows the error, a retry button and download buttons.

**Progress saving.** After every completed block the page (1) saves its state in the browser (localStorage) and (2) uploads `<ID>_<session>_progress_b<N>.csv` with all trials so far, in the background. If the tab closes or the page reloads, opening the link again on the same computer (within 6 hours) offers *Continue my session* (same order, practice not repeated; the interrupted block restarts from its beginning and its partial data is discarded) or *Start over*. A session that finished but failed to upload offers *Save my answers*. Rows record `resumes` (how many times the session was resumed). For analysis, use the final `_trials.csv` when it exists, otherwise the highest-numbered `_progress_b<N>` file for that session.

## Notes
- Williams design balances position and first-order carry-over across every 10 participants; block position is still in the data as a covariate.
- Hearing and volume are self-reported and self-set.

## Tests
Browser tests (Playwright) check every feature on six device profiles: desktop (1920×1080), laptop (1366×768), iPad portrait and landscape, and Android and iPhone phones. In CI the iPhone, iPad and Mac are also tested on the real Safari engine (WebKit). A fake clock skips the 30 s lead-ins and digit timings, so a complete session runs in about 30 seconds. The data server is always blocked, so tests never upload anything.

```
npm ci
npx playwright install chromium     # add webkit for the Safari-engine projects (PW_WEBKIT=1)
npm test                            # everything, all devices
npm run test:desktop                # desktop + laptop
npm run test:tablet                 # iPad portrait + landscape
npm run test:mobile                 # Android + iPhone
npm run test:smoke                  # quick checks; BASE_URL=https://... runs them against a live site
```

| File | Checks |
|---|---|
| `tests/core-flow.spec.js` | The experiment is unchanged: full session (practice, 5 blocks of 8 lists in Williams order, ratings, results, both CSVs) and resume after reload |
| `tests/intro.spec.js` | Music Course question, required name and roll number for Yes, optional roll number for No, 10 digits exactly, anonymous IDs, recorded fields |
| `tests/setup-flow.spec.js` | Page order intro → theme → volume → practice; System by default; instant preview; theme recorded; resume path |
| `tests/theme.spec.js` | System/Light/Dark, following the device live, remembered across pages, switcher on `test.html`, colour contrast in both themes |
| `tests/progress.spec.js` | Bar only on the first page of each phase, correct labels, only increases, resumed sessions |
| `tests/responsive.spec.js` | No sideways scrolling, touch targets ≥ 44 px, inputs ≥ 16 px (no iPhone zoom), keypad fits the screen |
| `tests/smoke.spec.js` | Pages, theme files and music files load (also run against the live site) |

## CI/CD
`.github/workflows/ci-cd.yml` runs on every push and pull request:
1. **Browser tests**, in parallel: desktop + laptop, iPad, phones, and the Safari engine (iPhone, iPad, Mac). Test reports are kept as artifacts.
2. **Analysis pipeline** on simulated data (`simulate.py` → `analyze.py`), checking the exclusions and the final sample.
3. **Site bundle**: only the served files, smoke-tested, uploaded as an artifact.
4. **Deploy** (main only). GitHub Pages currently publishes `main` by itself (Settings → Pages → "Deploy from a branch"), so a push to main goes live whether or not the tests pass. To publish only after every test passes, set Settings → Pages → Source to **GitHub Actions** and add the repository variable `PAGES_DEPLOY` = `actions` (Settings → Secrets and variables → Actions → Variables). Also recommended: protect `main` so pull requests need the CI checks to pass.
5. **Live check** (main only): waits until GitHub Pages serves the new commit, then runs the smoke tests against the live site on desktop, laptop, iPad and phones (Chromium and Safari engine). Set the variable `LIVE_URL` if the site moves to another address.

Development happens on the `dev` branch; merge into `main` (ideally through a pull request with green CI) to publish.

