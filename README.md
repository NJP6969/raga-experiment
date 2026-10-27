# Music and Memory Task

Static page, no install. Open `index.html` in Chrome or Edge, or host the folder (GitHub Pages, any shared drive web server). Audio autoplay needs a click first, and the page always has one. Works on phones, tablets (iPad), laptops and desktops, in a light or dark theme.

The site itself is `index.html` (the task), `test.html` (stimulus check, for researchers), `template.html` (starter page for new pages), `assets/` (design tokens, shared styles and theme switching) and `stimuli/`. Everything else (`tests/`, `tools/`, `package.json`, `playwright.config.js`) is only for testing and building and is not needed to run the task.

## Stimuli
Real recordings since 27 Oct 2026, built by `tools/make_real_stimuli.py`. Each piece is cut, time-stretched with Rubber Band (ffmpeg `rubberband` filter, pitch unchanged) to 60 and 100 BPM, made to loop seamlessly (2 s crossfade of the end into the start) and RMS-matched to -20 dBFS.

| File | Condition |
|---|---|
| `A_raga_slow.mp3` | Indian: Ramana Balachandhran (veena) with Patri Satish Kumar (mridangam), "Emi Neramu" (Tyagaraja, raga Shankarabharanam, the Western major scale), from the First Edition Arts recording (YouTube aJsywTs7Vuk), 23:10-27:50 of the video. Original pulse 78 BPM, stretched x0.77 to 60 BPM |
| `B_raga_fast.mp3` | Same clip, x1.28 to 100 BPM |
| `C_western_slow.mp3` | Western: "Almost Bliss" by Kevin MacLeod (incompetech.com, CC BY 4.0), guitars and percussion, A major. Original 89 BPM, x0.67 to 60 BPM |
| `D_western_fast.mp3` | Same piece, x1.12 to 100 BPM |

Quiet (E) is silence. The veena recording is copyrighted; it is used here for a one-off class study, and permission from First Edition Arts should be sought before any wider use.

Why real recordings and time-stretching: the music teacher judged the generated gamakas unconvincing, the same tune does not exist in both styles, and real Carnatic pieces nearly all sit at a 65-95 BPM pulse ("fast" means more notes per beat), so a 2:1 contrast between two real pieces could not be found. Stretching one recording to two tempos keeps the melody constant within each style.

The earlier generated stimuli (violin samples with coded gamakas, 60/120 BPM) are made by `make_stimuli.py` and are in the git history before 27 Oct 2026.
## Flow
Every information page has the same frame: a site header (the study name, plus the progress bar on the first page of each phase), a page heading with a short introduction, the content in separate cards, the buttons at the end, and a footer ("Questions about this study?" with the contact, or "ask your course instructor"). During the lists, lead-ins and rests the header and footer are hidden, so only the task is on screen.

0. **Information and consent**: six short steps, each fitting on one phone screen, with *← Back* and the step count above the heading and *Next* below: (1) **Welcome**: what the study is about, about 18 minutes, phone/tablet/computer, headphones; (2) **What you'll do**: the five parts; (3) **Before you start**: headphones and a quiet place, keep the page in front, set the volume once, continue within 6 hours if it closes; (4) **Your data**: what is and isn't recorded, and where it goes (DataPipe, then the study's Google Drive folder; progress kept in the browser until then); (5) **Your choices**: voluntary, finished blocks saved as you go, names and roll numbers removed before analysis or sharing, questions and removing answers later; (6) **Consent**: three statements, all of which must be ticked before *I agree, continue*. *I don't want to take part* ends on a thank-you page (nothing is recorded; the information can be read again). Nothing is saved or sent before consent. The consent time is recorded (`consent_time`).
   **Before running the study, fill in `STUDY` at the top of the script in `index.html`**: `team` (who runs it), `contact` (an email for questions and removal requests; also shown in the footer) and `ethics` (approval text). Empty ones are left out; without a contact, participants are told to ask their course instructor.
1. **About you**. First question: **"Are you part of the Music Course?"** Yes → full name and roll number, both required. No → only the roll number field is shown, and it is optional. A roll number, when given, must be **exactly 10 digits** (the field keeps digits only, stops at 10 and shows an error if left incomplete). Then Carnatic and Hindustani familiarity, training, hearing check. Names and roll numbers link a student's sessions and record course participation; both must be removed before data are shared. Without a roll number the session gets a unique anonymous ID `anon-<session>`, so anonymous students are never merged in the analysis. Works on phones, tablets and computers: answers are entered on an on-screen keypad (1–9, –, ⌫, Done) or a physical keyboard; the device (`device`: touch/computer) and input method per list (`input`: keypad/keyboard) are recorded. On the Begin tap all tracks are unlocked for iPhone playback, and the screen is kept awake (Wake Lock) during the session. (Earlier versions told phone and tablet users to use a laptop; since the on-screen keypad, phones and tablets are supported.)
2. Setup: **choose a theme** (System, Light or Dark). Until the participant picks, the page follows the device setting (System). The page changes as soon as an option is picked, and a preview shows a digit, the keypad and a rating scale in that theme, so participants can compare before continuing. The choice is remembered on that device (also on `test.html`) and recorded (`theme`, `theme_resolved`).
3. Order assignment: one of 10 Williams-design orders of the 5 conditions (each condition appears in each position twice and directly follows every other condition twice). Taken in rotation from DataPipe's condition counter when it is switched on (set it to 10 conditions); otherwise random. Recorded as `order_row`, `order`, `order_source`.
4. Volume check with a music sample. All four tracks start downloading here; each block waits until its track can play through.
5. Practice ("testing") without music: 2 serial-recall lists with feedback, then one baseline "right now" alertness and mood rating (logged as block 0, condition `baseline`).
6. Five blocks. Each block: 30 s listening → "Numbers" cue → **serial recall**, 8 lists of 9 digits (all of 1–9 in random order, no runs like 3-4-5; 0.75 s on, 0.25 s off; "List k of 8" shown; type them back in order, `-` for forgotten ones, all 9 positions required, no time limit) → ratings, every point labelled ("during this block" alertness and mood, and "how Indian" for music blocks) → 20 s rest ending with a soft chime. Music plays from the start of the block through the lists.
7. Results table and upload.

**Progress bar.** The bar at the top appears only on the first page of each phase, with its name and how much of the whole session is done: Intro, Setup (theme), Practice, Questions before the task (baseline rating), About the task (before the blocks and at the start of each block), Questions after each block, Finished. It is hidden on every other page (volume, lists, answers, lead-in, rests), so nothing distracts during the task. It only goes up; a resumed session continues from the progress it had reached.

**Theme and colours.** A calm palette (warm stone neutrals, one muted teal accent, serif headings) in a light and a dark version, from the design system below; all text meets WCAG AA contrast in both. `assets/theme.js` applies the choice before the page draws (no flash) and follows the device live when System is chosen. The resume page also leads through the theme page, with the saved choice selected.

About 18 minutes in total. Leaving the page mid-session triggers a "leave site?" prompt; switching tabs during a block shows a warning on return and is recorded (`tab_hidden_count`, and `tab_hidden_so_far` per list).

## Design system
Every page gets its look from three files, loaded in this order in `<head>`:

```
<link rel="stylesheet" href="assets/tokens.css">
<link rel="stylesheet" href="assets/theme.css">
<script src="assets/theme.js"></script>
```

| File | What it is |
|---|---|
| `assets/tokens.json` | **The source.** Colours (a `light` and a `dark` set with the same names), fonts, type sizes, spacing, radii and motion, in the W3C Design Tokens (DTCG) format, so it imports into Tokens Studio for Figma, Style Dictionary and other token tools |
| `assets/tokens.css` | Generated from `tokens.json` by `npm run tokens` (`tools/build-tokens.js`, no dependencies). Never edit by hand; a test fails if it is out of date |
| `assets/theme.css` | Shared styles built only from the tokens: site header and footer (`.site-header`, `.brand`, `.site-footer`), page heading (`.page-head`, `.eyebrow`, `.lead`), multi-step row (`.page-nav`, `.back-link`, `.step-count`), cards, button rows (`.actions`; `.secondary` for outlined buttons), numbered steps (`.steps`), ticked lists (`.checklist`), label and text pairs (`.facts`), large tick boxes (`.checks`, `.check`), fields, Yes/No choice (`.seg`), notices (`.warn`), tables, progress bar, theme switch (`.theme-switch`) |
| `assets/theme.js` | System / Light / Dark choice, remembered across pages; wires up any `.theme-switch` on the page |
| `template.html` | Starter page and component sheet: copy it to make a new page. Shows every component and every colour token in both themes |

To restyle every page at once, edit `assets/tokens.json` and run `npm run tokens`. Pages add only their own layout and never hard-code a colour (the tests check this). The classes `.theme-light` and `.theme-dark` give a single element that palette whatever the page shows (used for the theme swatches).

## URL options
- `?fast=1` shortens lead-in and rest (3 s and 2 s) for piloting.
- `?row=3` forces order 1–10 (Williams design). Default: DataPipe rotation, else random.
- `?nosave=1` runs without uploading (data can still be downloaded at the end).

## Output
At the end the page uploads two CSVs to DataPipe (experiment `hmU1FxSIMrPB`), which stores them in its Google Drive folder:
- `<ID>_<session>_trials.csv`: one row per recall list (stimulus, response, correct positions, response time) and rating, with condition, block position, order, `consent_time` (when the participant agreed, ISO time), Carnatic and Hindustani familiarity and training, `music_course` (1 = yes, 0 = no), `full_name` (empty when not in the course), `theme` (system/light/dark) and `theme_resolved` (light/dark actually shown).
- `<ID>_<session>_blocks.csv`: per-block summary (recall proportion correct in position, perfect lists, ratings, tab_hidden_count, audio_ok, music_course, full_name, theme).

`<ID>` is the roll number, or `anon-<session>` for students outside the course who gave none. `full_name` and roll numbers are personal data: remove them before sharing. The analysis never copies names into its outputs, but roll numbers stay in `clean_digit_level.csv` (column `participant`).

`session` is random per run, so two students typing the same ID never overwrite each other. Runs with `?fast=1` are prefixed `TEST_` and have `test_run = 1`; `?nosave=1` uploads nothing. If the upload fails, the page shows the error, a retry button and download buttons.

**Progress saving.** After every completed block the page (1) saves its state in the browser (localStorage) and (2) uploads `<ID>_<session>_progress_b<N>.csv` with all trials so far, in the background. If the tab closes or the page reloads, opening the link again on the same computer (within 6 hours) offers *Continue my session* (same order, practice not repeated; the interrupted block restarts from its beginning and its partial data is discarded) or *Start over*. A session that finished but failed to upload offers *Save my answers*. Rows record `resumes` (how many times the session was resumed). For analysis, use the final `_trials.csv` when it exists, otherwise the highest-numbered `_progress_b<N>` file for that session.

## Notes
- Williams design balances position and first-order carry-over across every 10 participants; block position is still in the data as a covariate.
- Hearing and volume are self-reported and self-set.

## Tests
Browser tests (Playwright) check every feature on six device profiles: desktop (1920×1080), laptop (1366×768), iPad portrait and landscape, and Android and iPhone phones. Projects for the real Safari engine (WebKit) on iPhone, iPad and Mac are included but not run by default and have not been checked (`PW_WEBKIT=1` turns them on). A fake clock skips the 30 s lead-ins and digit timings, so a complete session runs in about 30 seconds. The data server is always blocked, so tests never upload anything.

```
npm ci
npx playwright install chromium     # add webkit for the Safari-engine projects (PW_WEBKIT=1)
npm run serve                       # the site at http://127.0.0.1:4173/ (try index.html?nosave=1&fast=1: nothing uploads)
npm run tokens                      # rebuild assets/tokens.css after editing assets/tokens.json
npm test                            # everything, all devices
npm run test:desktop                # desktop + laptop
npm run test:tablet                 # iPad portrait + landscape
npm run test:mobile                 # Android + iPhone
npm run test:smoke                  # quick checks; BASE_URL=https://... runs them against a live site
```

| File | Checks |
|---|---|
| `tests/core-flow.spec.js` | The experiment is unchanged: full session (practice, 5 blocks of 8 lists in Williams order, ratings, results, both CSVs) and resume after reload |
| `tests/intro.spec.js` | About you page: Music Course question, required name and roll number for Yes, optional roll number for No, 10 digits exactly, anonymous IDs, recorded fields |
| `tests/setup-flow.spec.js` | Page order intro → theme → volume → practice; System by default; instant preview; theme recorded; resume path |
| `tests/theme.spec.js` | System/Light/Dark, following the device live, remembered across pages, switcher on `test.html`, colour contrast in both themes |
| `tests/progress.spec.js` | Bar only on the first page of each phase, correct labels, only increases, resumed sessions |
| `tests/responsive.spec.js` | No sideways scrolling, touch targets ≥ 44 px, inputs ≥ 16 px (no iPhone zoom), keypad fits the screen |
| `tests/consent.spec.js` | Information and consent: six steps in order, each with its button visible without scrolling, Back works, all the information is there, all three statements required, declining records nothing, header and footer hidden during the task |
| `tests/design.spec.js` | `tokens.css` matches `tokens.json`; light and dark name the same colours; no hard-coded colours in the pages; template page components, colour table and theme switch; theme swatches show their own palette |
| `tests/smoke.spec.js` | Pages, theme files and music files load (with `BASE_URL`, also against the live site) |

## Publishing
GitHub Pages publishes `main` (Settings → Pages → "Deploy from a branch"), so anything merged into `main` goes live straight away. Run `npm test` before merging.

Development happens on the `dev` branch; merge into `main` (after `npm test` passes) to publish.

