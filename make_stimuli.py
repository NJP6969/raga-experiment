"""Compose the stimuli as MIDI and render them with sampled instruments (FluidSynth).

One composed piece of 16 teentaal cycles (256 beats) in Raga Bhupali (S R G P D; Sa = G4):
sthayi -> development -> antara (upper register) -> tans (fast runs) -> return to sthayi.
No two cycles are the same. The melody (notes, timing, dynamics, humanization) is identical in
all four conditions; only the arrangement and tempo change.

  Raga:    flute melody with meend (pitch-bend glides), kan (grace notes) and vibrato,
           tanpura-style drone (sitar patch), tabla teentaal theka with fills (Tabla.sf2).
  Western: the same melody on piano, no ornaments; piano left-hand broken chords, bass,
           drum kit. Chords use only the five Bhupali pitches (G, Em, Asus4, Dsus2).
  Slow = 60 BPM (piece plays once per file), fast = 120 BPM (piece plays twice per file).

Every file is 256 s and loops seamlessly (rendered three times, middle copy kept).
Outputs: stimuli/*.mp3 (RMS-matched) and midi/*.mid (full arrangement, for editing in a DAW/MuseScore).

Usage:
  python make_stimuli.py --fluidsynth PATH/fluidsynth.exe --gm PATH/GeneralUser-GS.sf2 --tabla PATH/Tabla.sf2
Needs: numpy, mido, soundfile.  Soundfonts: GeneralUser GS (free licence), Tabla.sf2 from the CPAN
module Music::Percussion::Tabla (Artistic License 2.0).
"""
import argparse, math, os, random, subprocess, tempfile
import numpy as np
import mido
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 44100
FILE_S = 256.0
SA = 67                                   # G4
SC = [0, 2, 4, 7, 9]
NAMES = {"P_": -2, "D_": -1, "S": 0, "R": 1, "G": 2, "P": 3, "D": 4, "S^": 5, "R^": 6, "G^": 7}


def pitch(i):
    return SA + 12 * (i // 5) + SC[i % 5]


def parse(s):
    out = []
    for tok in s.split():
        k = len(tok.rstrip("0123456789."))
        out.append((NAMES[tok[:k]], float(tok[k:])))
    assert abs(sum(b for _, b in out) - 4) < 1e-9, s
    return out


# ---------------- composition ----------------
POOLS = {
    "STH": ["S1 R1 G2", "G1 R1 S1 D_1", "D_1 S1 R1 G1", "S2 R1 G1", "G2 R1 S1", "R1 G1 P2",
            "P1 G1 R1 G1", "G1 P1 G1 R1", "S0.5 R0.5 G1 R1 S1", "D_0.5 S0.5 R1 G2", "G1.5 R0.5 S2",
            "P2 G1 R1", "R0.5 G0.5 P1 G1 R1", "G2 P1 G1", "P_1 D_1 S2", "S1 D_1 S1 R1"],
    "DEV": ["G1 P1 D2", "P1 G1 P1 D1", "G0.5 P0.5 D1 P1 G1", "R1 G1 P1 D1", "D1 P1 G1 P1",
            "P1.5 G0.5 R1 G1", "G0.5 R0.5 G0.5 P0.5 D1 P1", "D2 P1 G1", "S1 R1 G1 P1", "P1 D1 P1 G1"],
    "ANT": ["P1 D1 S^2", "S^1 D1 P1 G1", "D1 S^1 R^1 S^1", "S^2 D1 P1", "P1 D1 S^1 R^1", "G^1 R^1 S^2",
            "S^0.5 R^0.5 S^1 D1 P1", "P1.5 D0.5 S^2", "R^1 S^1 D1 P1", "S^1 R^1 G^1 R^1",
            "D0.5 S^0.5 R^1 S^1 D1", "G1 P1 D1 S^1"],
}
CAD = {"S": ["G1 R1 S2", "R1 G1 R1 S1", "D_1 S1 R0.5 G0.5 S1", "G0.5 R0.5 S1 D_1 S1", "P1 G1 R1 S1"],
       "S^": ["D1 P1 D1 S^1", "P1 D1 S^2", "G1 P1 D1 S^1"]}
MUKHDA = {0: "S1 R1 G2", 8: "P1 D1 S^2", 14: "S1 R1 G2"}
# (section, base velocity, cadence target for last vibhag)
PLAN = [("STH", 64, None), ("STH", 66, None), ("STH", 68, None), ("STH", 68, "S"),
        ("DEV", 72, None), ("DEV", 74, None), ("DEV", 78, None), ("DEV", 80, "S^"),
        ("ANT", 84, None), ("ANT", 86, None), ("ANT", 88, None), ("ANT", 84, "S"),
        ("TAN", 92, None), ("TAN", 94, "S"),
        ("STH", 74, None), ("STH", 68, "S")]
CYCLE_BEATS = 16
PIECE_BEATS = CYCLE_BEATS * len(PLAN)


def tan(rng):
    s = rng.randint(-1, 4)
    kind = rng.choice(["updown", "downup", "zigzag", "asc"])
    seq = {"updown": [s, s + 1, s + 2, s + 3, s + 4, s + 3, s + 2, s + 1],
           "downup": [s + 4, s + 3, s + 2, s + 1, s, s + 1, s + 2, s + 3],
           "zigzag": [s, s + 1, s, s + 2, s + 1, s + 3, s + 2, s + 4],
           "asc":    [s, s + 1, s + 2, s + 3, s + 2, s + 3, s + 4, s + 5]}[kind]
    shift = min(0, 7 - max(seq))                       # keep runs inside the range, no clamped repeats
    return [(i + shift, 0.5) for i in seq]


def compose(seed=11):
    rng = random.Random(seed)
    pools = {k: [parse(p) for p in v] for k, v in POOLS.items()}
    cads = {k: [parse(p) for p in v] for k, v in CAD.items()}
    recent, notes = [], []

    def pick(pool):
        cands = [p for p in pool if p not in recent[-6:]] or pool
        p = rng.choice(cands); recent.append(p); return p

    for c, (sec, base, cad) in enumerate(PLAN):
        for v in range(4):
            if v == 0 and c in MUKHDA:
                ph = parse(MUKHDA[c])
            elif v == 3 and cad:
                ph = pick(cads[cad])
            elif sec == "TAN":
                ph = tan(rng)
            else:
                ph = pick(pools[sec])
            pos = 0.0
            for idx, b in ph:
                vel = base + 5 * math.sin(math.pi * pos / 4) + rng.uniform(-4, 4) + (3 if b >= 2 else 0)
                notes.append({"beat": c * CYCLE_BEATS + v * 4 + pos, "beats": b, "idx": idx,
                              "vel": int(min(120, max(30, vel))), "cycle": c})
                pos += b
    hum = random.Random(99)
    for n in notes:                                    # shared humanization (seconds)
        n["jit"] = 0.0 if n["beat"] % CYCLE_BEATS == 0 else max(-0.02, min(0.02, hum.gauss(0, 0.008)))
    return notes


# ---------------- arrangement: each stem = (notes[(on, off, pitch, vel)], ctrl[(t, msg)]) ----------------
def melody_times(notes, spb, reps):
    """Onsets for the piece repeated `reps` times inside one file."""
    piece_s = PIECE_BEATS * spb; out = []
    for r in range(reps):
        for n in notes:
            out.append(dict(n, on=r * piece_s + n["beat"] * spb + n["jit"], dur=n["beats"] * spb))
    return out


def flute(mel, file_s):
    rng = random.Random(5)
    notes = []
    ctrl = [(0, mido.Message("control_change", control=c, value=v)) for c, v in
            ((101, 0), (100, 0), (6, 12), (38, 0), (101, 127), (100, 127), (11, 110))]
    plan = []
    for i, n in enumerate(mel):
        prev = mel[i - 1] if i else mel[-1]
        kan = n["beats"] >= 1 and n["idx"] < 7 and rng.random() < 0.22
        meend = (not kan) and n["beats"] >= 1 and abs(pitch(prev["idx"]) - pitch(n["idx"])) <= 5 \
            and prev["idx"] != n["idx"] and rng.random() < 0.45
        plan.append((kan, meend))
    bent = False
    for i, n in enumerate(mel):
        kan, meend = plan[i]
        on = n["on"]; nxt = mel[i + 1]["on"] if i + 1 < len(mel) else file_s
        nkan, nmeend = plan[i + 1] if i + 1 < len(mel) else plan[0]
        p = pitch(n["idx"])
        off = nxt if nmeend else nxt + 0.015
        if kan:
            notes.append((on, on + 0.075, pitch(n["idx"] + 1), max(30, n["vel"] - 12)))
            on += 0.06
        if meend:
            prev = mel[i - 1] if i else mel[-1]
            semis = pitch(prev["idx"]) - p; g = min(0.25, 0.45 * n["dur"])
            for k in range(11):
                v = semis * (0.5 + 0.5 * math.cos(math.pi * k / 10))
                ctrl.append((on - 0.002 + g * k / 10, mido.Message("pitchwheel", pitch=int(max(-8192, min(8191, v / 12 * 8192))))))
            bent = True
        elif bent:
            ctrl.append((on - 0.002, mido.Message("pitchwheel", pitch=0))); bent = False
        if n["dur"] >= 1.2:                            # delayed vibrato on long notes
            for k in range(6):
                ctrl.append((on + n["dur"] * (0.4 + 0.06 * k), mido.Message("control_change", control=1, value=9 * k)))
            ctrl.append((nxt - 0.003, mido.Message("control_change", control=1, value=0)))
        notes.append((on, off, p, n["vel"]))
    return notes, ctrl


def piano_melody(mel, file_s):
    notes = []
    for i, n in enumerate(mel):
        nxt = mel[i + 1]["on"] if i + 1 < len(mel) else file_s
        notes.append((n["on"], nxt - (0.0 if n["beats"] >= 2 else 0.02), pitch(n["idx"]), min(127, n["vel"] + 4)))
    return notes, []


def tanpura(file_s):
    rng = random.Random(7); notes = []
    for k, t in enumerate(np.arange(0, file_s, 1.0)):
        p = [SA - 17, SA - 12, SA - 12, SA - 24][k % 4]            # Pa, Sa, Sa, low Sa
        on = t + rng.uniform(-0.01, 0.01)
        notes.append((max(0, on), on + 3.8, p, 48 + rng.randint(-5, 5)))
    return notes, []


TABLA = {"ge": [65, 66, 76], "ke": [64, 77, 79], "na": [78, 81], "ta": [71, 75, 85],
         "ti": [61, 68, 70, 72, 82, 86], "tin": [60, 63, 83, 87], "tun": [88]}
THEKA = ["dha", "dhin", "dhin", "dha", "dha", "dhin", "dhin", "dha",
         "dha", "tin", "tin", "ta", "ta", "dhin", "dhin", "dha"]
TABLA_FILL = ["ta", "ke", "ti", "ta", "ke", "ti", "dha", "dha"]
BOL_VEL = {"dha": 100, "dhin": 96, "tin": 84, "ta": 88, "ti": 60, "ke": 60}


def tabla(spb, reps):
    rng = random.Random(13); notes = []
    piece_s = PIECE_BEATS * spb

    def strike(t, bol, vel):
        parts = {"dha": ["ge", "ta"], "dhin": ["ge", "tin"]}.get(bol, [bol])
        for part in parts:
            v = int(min(127, max(20, vel + rng.randint(-6, 6) - (8 if part == "ge" else 0))))
            notes.append((t, t + 1.2, rng.choice(TABLA[part]), v))

    for r in range(reps):
        for b in range(PIECE_BEATS):
            c, pos = divmod(b, CYCLE_BEATS); t = r * piece_s + b * spb
            dense = PLAN[c][0] == "TAN"
            if c % 4 == 3 and pos >= 12:
                k = (pos - 12) * 2
                strike(t, TABLA_FILL[k], 92); strike(t + spb / 2, TABLA_FILL[k + 1], 86)
                continue
            strike(t, THEKA[pos], 112 if pos == 0 else BOL_VEL[THEKA[pos]])
            if dense or pos in (1, 2, 5, 6, 13, 14):
                strike(t + spb / 2, "ti" if pos % 2 else "ke", 58)
    return notes, []


CHORDS = {"G": [55, 59, 62], "Em": [52, 55, 59], "Asus4": [57, 62, 64], "Dsus2": [50, 52, 57]}
ROOT = {"G": 43, "Em": 40, "Asus4": 45, "Dsus2": 38}
PROG = {"STH": ["G", "Em", "Asus4", "Dsus2"], "DEV": ["Em", "G", "Dsus2", "Asus4"],
        "ANT": ["Em", "Dsus2", "G", "Asus4"], "TAN": ["G", "Dsus2", "Em", "Asus4"]}


def chord_at(c, j):
    if c == len(PLAN) - 1 and j == 3:
        return "G"
    return PROG[PLAN[c][0]][j]


def western_backing(spb, reps):
    rng = random.Random(17)
    lh, bass, drums = [], [], []
    piece_s = PIECE_BEATS * spb

    def hit(t, note, vel, ln=0.3):
        drums.append((t, t + ln, note, int(min(127, max(15, vel + rng.randint(-6, 6))))))

    for r in range(reps):
        for k in range(PIECE_BEATS // 4):                         # bars
            c, j = divmod(k, 4); sec = PLAN[c][0]; ch = chord_at(c, j)
            t0 = r * piece_s + k * 4 * spb
            # piano left hand: broken chord in eighths
            tones = CHORDS[ch]; order = [0, 1, 2, 1, 0 + 3, 1, 2, 1]
            for e, o in enumerate(order):
                p = tones[o % 3] + (12 if o >= 3 else 0)
                t = t0 + e * spb / 2
                lh.append((t, t + spb / 2 + 0.05, p, 46 + (6 if e % 4 == 0 else 0) + rng.randint(-4, 4)))
            # bass
            root = ROOT[ch]; fifth = tones[2] - 12
            for beat, ln, p in ((0, 1.5, root), (1.5, 0.5, fifth), (2, 1.0, root), (3, 1.0, root + 12 if j % 2 else fifth)):
                bass.append((t0 + beat * spb, t0 + (beat + ln) * spb - 0.03, p, 78 + rng.randint(-6, 6)))
            # drums
            fill = (c % 4 == 3 and j == 3)
            if j == 0 and c % 4 == 0:
                hit(t0, 49, 96, 2.0)
            for e in range(8):                                   # eighth-note grid
                t = t0 + e * spb / 2; beat = e / 2
                if fill and e >= 4:
                    hit(t, [50, 48, 47, 45][e - 4], 92); continue
                if sec == "ANT":
                    hit(t, 51, 70 if e % 2 == 0 else 58)
                elif sec == "TAN":
                    hit(t, 42, 70 if e % 2 == 0 else 52); hit(t + spb / 4, 42, 40)
                else:
                    hit(t, 42, (62 if e % 2 == 0 else 46) - (6 if sec == "STH" else 0))
                if e == 7 and j % 2 == 1 and sec == "DEV":
                    hit(t, 46, 66)
                if beat in (0, 2) or (sec in ("ANT", "TAN") and e == 3) or (j == 2 and e == 5):
                    hit(t, 36, 100)
                if beat in (1, 3):
                    hit(t, 37 if sec == "STH" else 38, 84 if sec != "STH" else 70)
                if sec == "TAN" and e in (3, 6):
                    hit(t, 38, 40)                                   # ghost notes
    return (lh, []), (bass, []), (drums, [])


# ---------------- MIDI + rendering ----------------
def fix_overlaps(notes):
    """A note-off must not land after the next note-on of the same pitch."""
    by = {}
    for n in sorted(notes):
        by.setdefault(n[2], []).append(list(n))
    out = []
    for lst in by.values():
        for a, b in zip(lst, lst[1:]):
            a[1] = min(a[1], b[0] - 0.004)
        out += [tuple(x) for x in lst if x[1] > x[0]]
    return out


def shifted(stem, dt):
    notes, ctrl = stem
    return [(a + dt, b + dt, p, v) for a, b, p, v in notes], [(t + dt, m) for t, m in ctrl]


def write_midi(path, tracks, bpm, end_s):
    """tracks: list of (name, program, channel, (notes, ctrl))."""
    mid = mido.MidiFile(type=1, ticks_per_beat=480)
    meta = mido.MidiTrack(); meta.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(bpm), time=0))
    mid.tracks.append(meta)
    tick = lambda t: max(0, round(t * bpm / 60 * 480))
    for name, prog, ch, (notes, ctrl) in tracks:
        tr = mido.MidiTrack(); tr.append(mido.MetaMessage("track_name", name=name, time=0))
        if prog is not None:
            tr.append(mido.Message("program_change", program=prog, channel=ch, time=0))
        ev = [(tick(t), 1, m) for t, m in ctrl]
        for on, off, p, v in fix_overlaps(notes):
            ev.append((tick(on), 2, mido.Message("note_on", note=p, velocity=int(v))))
            ev.append((tick(off), 0, mido.Message("note_off", note=p, velocity=0)))
        ev.append((tick(end_s), 3, mido.Message("control_change", control=7, value=100)))
        ev.sort(key=lambda e: (e[0], e[1]))
        last = 0
        for tk, _, m in ev:
            tr.append(m.copy(channel=ch, time=tk - last)); last = tk
        mid.tracks.append(tr)
    mid.save(path)


def render(fs_exe, sf2, tracks, bpm, end_s, tmp):
    mpath = os.path.join(tmp, "stem.mid"); wpath = os.path.join(tmp, "stem.wav")
    write_midi(mpath, tracks, bpm, end_s)
    subprocess.run([os.path.abspath(fs_exe), "-ni", "-q", "-g", "0.4", "-r", str(SR), "-F", wpath, sf2, mpath], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    y, sr = sf.read(wpath, always_2d=True); assert sr == SR
    n = int(end_s * SR)
    return np.pad(y, ((0, max(0, n - len(y))), (0, 0)))[:n]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fluidsynth", required=True); ap.add_argument("--gm", required=True); ap.add_argument("--tabla", required=True)
    a = ap.parse_args()
    out_dir = os.path.join(HERE, "stimuli"); midi_dir = os.path.join(HERE, "midi")
    os.makedirs(out_dir, exist_ok=True); os.makedirs(midi_dir, exist_ok=True)
    notes = compose()
    COPIES = 3; end_s = FILE_S * COPIES
    mixes = {}
    with tempfile.TemporaryDirectory() as tmp:
        for tag, bpm in (("slow", 60), ("fast", 120)):
            spb = 60 / bpm; reps = int(round(FILE_S / (PIECE_BEATS * spb)))
            mel = melody_times(notes, spb, reps)
            stems = {"flute": flute(mel, FILE_S), "tanpura": tanpura(FILE_S), "tabla": tabla(spb, reps),
                     "piano": piano_melody(mel, FILE_S)}
            stems["lh"], stems["bass"], stems["drums"] = western_backing(spb, reps)
            # three back-to-back copies of the file; keep the middle one => seamless loop
            loop = {k: tuple(sum(x, []) for x in zip(*[shifted(v, i * FILE_S) for i in range(COPIES)])) for k, v in stems.items()}
            spec = {  # stem: (soundfont, program, channel, gain, pan 0..1)
                "flute": (a.gm, 73, 0, 1.0, 0.5), "tanpura": (a.gm, 104, 0, 0.42, 0.35), "tabla": (a.tabla, 0, 0, 0.8, 0.62),
                "piano": (a.gm, 0, 0, 1.0, 0.5), "lh": (a.gm, 0, 0, 0.5, 0.4), "bass": (a.gm, 33, 0, 0.55, 0.5),
                "drums": (a.gm, None, 9, 0.6, 0.5)}
            audio = {}
            for k, (sf2, prog, ch, gain, pan) in spec.items():
                y = render(a.fluidsynth, sf2, [(k, prog, ch, loop[k])], bpm, end_s, tmp)
                m = y.mean(1)[int(FILE_S * SR):int(2 * FILE_S * SR)]
                m = m / (np.sqrt(np.mean(m ** 2)) + 1e-12)
                audio[k] = np.stack([m * math.cos(pan * math.pi / 2), m * math.sin(pan * math.pi / 2)], 1) * gain * math.sqrt(2)
                print(f"  rendered {tag} {k}")
            mixes["A_raga_slow" if tag == "slow" else "B_raga_fast"] = audio["flute"] + audio["tanpura"] + audio["tabla"]
            mixes["C_western_slow" if tag == "slow" else "D_western_fast"] = audio["piano"] + audio["lh"] + audio["bass"] + audio["drums"]
            # one copy of the piece as an editable MIDI arrangement
            piece_s = PIECE_BEATS * spb
            cut = lambda st: ([n for n in st[0] if n[0] < piece_s], [c for c in st[1] if c[0] < piece_s])
            write_midi(os.path.join(midi_dir, f"raga_{tag}.mid"),
                       [("Flute (melody)", 73, 0, cut(stems["flute"])), ("Tanpura (sitar patch)", 104, 1, cut(stems["tanpura"])),
                        ("Tabla (Tabla.sf2 note map)", 0, 2, cut(stems["tabla"]))], bpm, piece_s)
            write_midi(os.path.join(midi_dir, f"western_{tag}.mid"),
                       [("Piano (melody)", 0, 0, cut(stems["piano"])), ("Piano (left hand)", 0, 1, cut(stems["lh"])),
                        ("Bass", 33, 2, cut(stems["bass"])), ("Drums", None, 9, cut(stems["drums"]))], bpm, piece_s)
    rms = {k: np.sqrt(np.mean(v ** 2)) for k, v in mixes.items()}
    target = min(0.1, *[0.89 / np.abs(v).max() * rms[k] for k, v in mixes.items()])
    for k, v in sorted(mixes.items()):
        y = v * (target / rms[k])
        sf.write(os.path.join(out_dir, k + ".mp3"), y, SR, format="MP3")
        print(f"{k}.mp3 rms={20*np.log10(np.sqrt(np.mean(y**2))):.1f} dBFS peak={20*np.log10(np.abs(y).max()):.1f} dBFS")


if __name__ == "__main__":
    main()
