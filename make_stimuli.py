"""Build the four music stimuli from real recorded samples.

Raga Mohanam (S R2 G3 P D2; the Carnatic counterpart of Bhupali, same five notes), Adi talam
(8 beats x 4 aksharas), Sa = Eb4 to match the tanpura and mridangam recordings.

One composed piece of 32 avartanams: pallavi with sangatis (each repeat more elaborate),
anupallavi (upper register), pallavi, kalpanaswaram-style passages ending in a mora, charanam,
pallavi, ending. The melody (notes, timing, dynamics) is identical in every condition.

  Indian style:  solo violin with continuous gamakas (jaru slides, kampita on Ri/Ga/Dha, the
                 'pa-sa-dha', 'pa-ga', 'ga-ri' approaches, sphuritam on repeated notes), notes in
                 just intonation, Sa and Pa unornamented; real tanpura; real mridangam strokes
                 (sarvalaghu-style accompaniment, moras into samam).
  Western style: the same violin samples and melody, equal temperament, one bow per note, no
                 slides; upright piano broken chords + cello (GeneralUser GS) + soft drum kit.
                 Chords use only the five Mohanam pitches (Eb, Cm, Fsus4, Bbsus2).
  Slow = 60 BPM (piece plays once per file), fast = 120 BPM (twice). Files are 256 s, loop
  seamlessly and are RMS-matched.

Samples (download once; see README):
  violin/     VSCO 2 Community Edition, solo violin Arco Vib (p), CC0
  mridangam/  IITM-CompMusic Mridangam Stroke Dataset, D# tonic (Freesound pack 14163), CC BY-NC 3.0
  tanpura_Eb.mp3  'Tambura_Eb_fat' by Kaczinski (Freesound 506312), CC0
Usage:
  python make_stimuli.py --assets DIR --fluidsynth PATH/fluidsynth.exe --gm PATH/GeneralUser-GS.sf2
Needs numpy, mido, soundfile.
"""
import argparse, glob, math, os, random, re, subprocess, tempfile
import numpy as np
import mido
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 44100
CR = 1000                                 # control rate for pitch curves (Hz)
FILE_S = 256.0
SA = 63                                   # Eb4
SC = [0, 2, 4, 7, 9]
NAMES = {"P_": -2, "D_": -1, "S": 0, "R": 1, "G": 2, "P": 3, "D": 4, "S^": 5, "R^": 6, "G^": 7, "P^": 8}
JI = {0: 0.0, 2: 3.9, 4: -13.7, 7: 2.0, 9: -15.6}          # cents from equal temperament
AV_BEATS = 8


def pitch(i):
    return SA + 12 * (i // 5) + SC[i % 5]


def ji_pitch(i):
    return pitch(i) + JI[SC[i % 5]] / 100


# ---------------- composition (swara notation; '~' = explicit kampita) ----------------
TOK = re.compile(r"(P_|D_|S\^|R\^|G\^|P\^|S|R|G|P|D)(~?)([\d.]+)$")
PALLAVI_1 = ["G~2 R1 S1 D_1 S1 R1 G1", "P1.5 G0.5 D~2 P1 G1 R~2"]
PALLAVI_2 = ["G~2 R1 S1 D_0.5 S0.5 R1 G1 P1", "P1 D0.5 P0.5 G1 D~2 P1 G0.5 R0.5 G1"]
PALLAVI_3 = ["G0.5 G0.5 R0.5 R0.5 S1 D_1 S0.5 S0.5 R0.5 R0.5 G2", "P0.5 P0.5 G0.5 G0.5 D~2 P0.5 P0.5 G0.5 G0.5 R~2"]
PALLAVI_4 = ["G~1 P1 D1 S^2 D1 P1 G1", "S^1 D~1 P1 G1 D~1 P1 G0.5 R0.5 S1"]
ANUPALLAVI = ["P1 D1 S^2 S^1 R^1 S^1 D1", "R^~2 S^1 D1 P1 D1 S^2", "S^1 R^1 G^~2 R^1 S^1 D~2",
              "S^1 D1 P1 G1 P1 D1 S^2", "S^0.5 S^0.5 R^0.5 R^0.5 G^~2 R^0.5 R^0.5 S^0.5 S^0.5 D~2",
              "S^1 D1 P1 G1 R1 G1 P0.5 G0.5 R1"]
SW_R1 = ["S0.5 S0.5 R0.5 R0.5 G0.5 G0.5 P0.5 P0.5 D0.5 D0.5 P0.5 P0.5 G0.5 G0.5 R0.5 R0.5"]
SW_R2 = ["D_0.5 S0.5 R0.5 G0.5 S0.5 R0.5 G0.5 P0.5 R0.5 G0.5 P0.5 D0.5 G0.5 P0.5 D0.5 S^0.5",
         "D0.5 G0.5 R0.5 G0.5 S0.5 R0.5 G1 P1 D0.5 P0.5 G1 R1"]
SW_R3 = ["S^0.5 D0.5 P0.5 G0.5 D0.5 P0.5 G0.5 R0.5 P0.5 G0.5 R0.5 S0.5 G0.5 R0.5 S0.5 D_0.5"]
MORA = "D_0.5 S0.5 R0.5 G0.5 P1 D_0.5 S0.5 R0.5 G0.5 P1 D_0.5 S0.5 R0.5 G0.5"
CHARANAM = ["D_2 S1 R1 G~2 R1 S1", "D_1 S1 R1 G1 P2 G1 R1", "G1 P1 D~2 P1 G1 R~2", "G1 R1 S1 D_1 P_1 D_1 S2"]
ENDING = ["P1 D1 S^1 D1 P1 G1 R1 G1", "G0.5 R0.5 S1 G0.5 R0.5 S1 G0.5 R0.5 S3"]
FORM = ([("pallavi", a) for a in PALLAVI_1 + PALLAVI_2 + PALLAVI_3 + PALLAVI_4]
        + [("anupallavi", a) for a in ANUPALLAVI]
        + [("pallavi", a) for a in PALLAVI_2]
        + [("swaram", a) for a in SW_R1] + [("pallavi", PALLAVI_1[0])]
        + [("swaram", a) for a in SW_R2] + [("pallavi", PALLAVI_1[0])]
        + [("swaram", a) for a in SW_R3] + [("mora", MORA)] + [("pallavi", PALLAVI_1[0])]
        + [("charanam", a) for a in CHARANAM]
        + [("pallavi", a) for a in PALLAVI_1]
        + [("ending", a) for a in ENDING])
N_AV = len(FORM)
PIECE_BEATS = N_AV * AV_BEATS
SECTION_VEL = {"pallavi": 70, "anupallavi": 82, "swaram": 86, "mora": 90, "charanam": 72, "ending": 76}


def parse(av):
    out = []
    for tok in av.split():
        m = TOK.match(tok)
        out.append((NAMES[m.group(1)], m.group(2) == "~", float(m.group(3))))
    assert abs(sum(b for *_, b in out) - AV_BEATS) < 1e-9, av
    return out


def compose():
    rng = random.Random(21); notes = []
    for a, (sec, av) in enumerate(FORM):
        pos = 0.0
        for idx, kamp, b in parse(av):
            vel = SECTION_VEL[sec] + 5 * math.sin(math.pi * (pos % 4) / 4) + rng.uniform(-3, 3) \
                + (3 if b >= 2 else 0) + (4 if b >= 1 and idx % 5 in (2, 4) else 0)
            notes.append({"beat": a * AV_BEATS + pos, "beats": b, "idx": idx, "kamp": kamp,
                          "vel": int(min(118, max(40, vel))), "sec": sec, "av": a})
            pos += b
    hum = random.Random(99)
    for n in notes:
        n["jit"] = 0.0 if n["beat"] % AV_BEATS == 0 else max(-0.015, min(0.015, hum.gauss(0, 0.006)))
    return notes


def timed(notes, spb, reps):
    piece_s = PIECE_BEATS * spb; out = []
    for r in range(reps):
        for n in notes:
            out.append(dict(n, on=r * piece_s + n["beat"] * spb + n["jit"]))
    for i, n in enumerate(out):
        nxt = out[i + 1]["on"] if i + 1 < len(out) else FILE_S + out[0]["on"]
        n["dur"] = nxt - n["on"]
    return out


# ---------------- gamaka engine ----------------
def eased(bps, n):
    """Pitch curve at CR from breakpoints [(t, p)], cosine-eased between points."""
    t = np.arange(n) / CR
    T = np.array([b[0] for b in bps]); P = np.array([b[1] for b in bps])
    k = np.clip(np.searchsorted(T, t, side="right") - 1, 0, len(T) - 1); k2 = np.minimum(k + 1, len(T) - 1)
    f = np.clip((t - T[k]) / np.maximum(T[k2] - T[k], 1e-9), 0, 1)
    return P[k] + (P[k2] - P[k]) * (0.5 - 0.5 * np.cos(np.pi * f))


def gamaka(n, prev, rng):
    """Breakpoints for one note in Carnatic style (Mohanam conventions)."""
    x, px, dur = n["idx"], prev["idx"], n["dur"]
    base, prevp = ji_pitch(x), ji_pitch(px)
    up, low = ji_pitch(x + 1), ji_pitch(x - 1)
    pc = x % 5
    if px == x:                                                     # janta: sphuritam flick from below
        return ([(0, low), (0.03, low), (0.055, base), (dur, base)] if pc not in (0, 3) else [(0, base), (dur, base)])
    short = dur < 0.3
    g = min(0.05 if short else 0.14, 0.3 * dur)
    if short or pc in (0, 3):                                       # Sa, Pa: steady, plain glide in
        return [(0, prevp), (g, base), (dur, base)]
    asc = prevp < base
    if pc == 4 and asc:                                             # 'pa-sa-dha'
        bps = [(0, prevp), (g, up), (g + min(0.12, 0.25 * dur), base)]
    elif not asc:                                                   # 'sa-dha', 'pa-ga', 'ga-ri'
        bps = [(0, up), (g, base)]
    else:
        bps = [(0, prevp), (g * 0.7, base)]
    if n["kamp"] or (n["beats"] >= 1.5 and rng.random() < 0.5):     # kampita towards the upper swara
        t, half, depth, k = bps[-1][0], 0.5 / 5.5, 0.85 * (up - base), 0
        while t + half < 0.8 * dur:
            t += half; k += 1
            bps.append((t, base + depth if k % 2 else base))
        if k % 2:
            bps.append((min(dur, t + half), base))
    bps.append((max(dur, bps[-1][0] + 1e-3), base))
    return bps


# ---------------- violin sampler ----------------
VIOLIN_NOTES = {"G3": 55, "A3": 57, "C4": 60, "E4": 64, "G4": 67, "A4": 69, "C5": 72, "E5": 76, "G5": 79, "A5": 81, "C6": 84}


class Violin:
    def __init__(self, folder):
        self.s, self.sus = {}, {}
        for name, m in VIOLIN_NOTES.items():
            y, sr = sf.read(os.path.join(folder, f"LLVln_ArcoVib_{name}_p.wav"), always_2d=True); assert sr == SR
            on = int(np.argmax(np.abs(y.mean(1)) > 0.1 * np.abs(y).max()))
            sus_rms = np.sqrt(np.mean(y[on + SR // 2: on + 3 * SR] ** 2))
            w = int(0.01 * SR); m_ = y.mean(1)
            env = np.sqrt(np.convolve(m_ ** 2, np.ones(w) / w, "same"))
            a50 = int(np.argmax(env > 0.5 * sus_rms))          # recorded bow attacks differ; keep only ~40 ms of it
            win = int(0.05 * SR); seg = m_[a50 + int(0.3 * SR):]
            db = 20 * np.log10(np.sqrt((seg[:len(seg) // win * win].reshape(-1, win) ** 2).mean(1)) + 1e-9)
            dips = np.where(db < np.median(db) - 6)[0]          # bow changes inside the recording
            clean_end = a50 + int(0.3 * SR) + (dips[0] * win if len(dips) else len(seg))
            self.s[m] = (y / (sus_rms + 1e-9) * 0.1, max(0, a50 - int(0.04 * SR)))
            self.sus[m] = (a50 + int(0.3 * SR), clean_end)

    def legato_start(self, src, need_s, rng):
        lo, hi = self.sus[src]
        room = hi - lo - int(need_s * 1.25 * SR)
        return lo + (int(rng.uniform(0, room)) if room > 0 else 0)

    def nearest(self, p):
        return min(self.s, key=lambda k: abs(k - p))

    def segment(self, curve, src, start):
        y, _ = self.s[src]
        n = int(len(curve) / CR * SR)
        rate = np.interp(np.arange(n) / SR, np.arange(len(curve)) / CR, 2 ** ((curve - src) / 12))
        pos = start + np.concatenate([[0], np.cumsum(rate[:-1])])
        over = pos[-1] - (len(y) - 2)
        if over > 0:                                    # start earlier in the sustain instead of running off the end
            pos -= min(over, max(0, start - self.s[src][1]))
            pos = np.minimum(pos, len(y) - 2)
        idx = np.arange(len(y))
        return np.stack([np.interp(pos, idx, y[:, 0]), np.interp(pos, idx, y[:, 1])], 1)


def add(buf, i0, sig):
    N = len(buf); i0 %= N; e = i0 + len(sig)
    if e <= N:
        buf[i0:e] += sig
    else:
        k = N - i0; buf[i0:] += sig[:k]; buf[:len(sig) - k] += sig[k:]


def violin_line(vln, mel, style, rng):
    N = int(FILE_S * SR); out = np.zeros((N, 2))
    XF = 0.03
    since_bow = 99.0
    for i, n in enumerate(mel):
        prev = mel[i - 1]
        dur = n["dur"]
        if style == "indian":
            bps = gamaka(n, prev, rng)
            bow = since_bow >= 1.2 or n["av"] != prev["av"] and n["sec"] != prev["sec"]
        else:
            bps = [(0, pitch(n["idx"])), (dur, pitch(n["idx"]))]
            bow = True
        since_bow = dur if bow else since_bow + dur
        tail = XF if style == "indian" else 0.09
        nc = int((dur + tail) * CR) + 2
        curve = eased(bps, nc)
        src = vln.nearest(pitch(n["idx"]))
        onset = vln.s[src][1]
        start = onset if bow else vln.legato_start(src, dur + tail, rng)
        sig = vln.segment(curve, src, start)
        L = len(sig); t = np.arange(L) / SR
        env = np.ones(L)
        if style == "indian":
            fi = int((0.012 if bow else XF) * SR); env[:fi] = np.sin(np.linspace(0, np.pi / 2, fi))
            fo = int(XF * SR); env[L - fo:] *= np.cos(np.linspace(0, np.pi / 2, fo))
            if dur > 0.8:
                env *= 1 + 0.12 * np.sin(np.pi * np.clip(t / dur, 0, 1))
        else:
            fi = int(0.005 * SR); env[:fi] = np.linspace(0, 1, fi)
            rel = np.clip((t - (dur - 0.02)) / 0.07, 0, 1); env *= np.cos(rel * np.pi / 2)
        gain = (n["vel"] / 90) ** 1.6
        add(out, int(n["on"] * SR), sig * (env * gain)[:, None])
    return out


# ---------------- mridangam ----------------
STROKES = ["Bheem", "Cha", "Dheem", "Dhin", "Num", "Ta", "Tha", "Tham", "Thi", "Thom"]
STROKE_GAIN = {"Tham": 1.0, "Thom": 0.95, "Dheem": 0.85, "Dhin": 0.8, "Num": 0.75, "Cha": 0.8,
               "Ta": 0.7, "Tha": 0.65, "Thi": 0.6, "Bheem": 0.8}
CELLS = {
    "sparse": ["Tham . . .", "Dhin . Num .", "Thom . Ta .", "Num . . Ta", "Dheem . . .", "Ta . Dhin ."],
    "medium": ["Tham . Ta Thi", "Dhin . Num .", "Thom . Ta Ta", "Dheem . Thi Num", "Ta Thi Thom .",
               "Num . Dhin Ta", "Cha . Num ."],
    "dense":  ["Ta Thi Ta Thi", "Thom Ta Thi Ta", "Tha Thi Num Ta", "Dhin Ta Thi Ta", "Num Ta Thi Ta", "Cha Thi Ta Thi"],
}
DENSITY = {"pallavi": "medium", "anupallavi": "medium", "swaram": "dense", "mora": "dense",
           "charanam": "sparse", "ending": "medium"}


class Mridangam:
    def __init__(self, folder):
        self.s = {}
        for st in STROKES:
            lst = []
            for p in sorted(glob.glob(os.path.join(folder, f"{st}_Dsh_*.mp3"))):
                y, sr = sf.read(p, always_2d=True); assert sr == SR
                if y.shape[1] == 1: y = np.repeat(y, 2, 1)
                on = int(np.argmax(np.abs(y.mean(1)) > 0.05 * np.abs(y).max()))
                y = y[max(0, on - int(0.003 * SR)): on + SR]
                f = int(0.02 * SR); y[-f:] *= np.linspace(1, 0, f)[:, None]
                lst.append(y / (np.abs(y).max() + 1e-9))
            assert lst, st
            self.s[st] = lst


def mridangam_events(mel, spb, reps, rng):
    """[(time_s, stroke, gain)] for one file."""
    ev = []
    piece_s = PIECE_BEATS * spb; ak = spb / 4
    for r in range(reps):
        grid = {}                                                   # akshara index -> stroke
        for a, (sec, _) in enumerate(FORM):
            first_pallavi = sec == "pallavi" and a < 2
            dens = "sparse" if first_pallavi else DENSITY[sec]
            for b in range(AV_BEATS):
                if sec == "mora":
                    break
                cell = rng.choice(CELLS[dens]).split()
                if b == 0:
                    cell[0] = "Tham"
                elif b in (4, 6) and cell[0] == ".":
                    cell[0] = rng.choice(["Dheem", "Thom", "Dhin"])
                for k, s in enumerate(cell):
                    if s != ".":
                        grid[(a * AV_BEATS + b) * 4 + k] = s
            if sec not in ("mora", "ending") and a % 4 == 3 and FORM[(a + 1) % N_AV][0] != "mora":
                phrase, gap = ["Ta", "Thi", "Thom"], 1                    # 3 x 3 + 2 x 1 = 11 aksharas
                end = (a + 1) * AV_BEATS * 4                             # next samam
                start = end - (3 * len(phrase) + 2 * gap) + 1
                for k in range(start, end): grid.pop(k, None)
                pos = start
                for rep in range(3):
                    for s in phrase:
                        grid[pos] = s; pos += 1
                    pos += gap
                grid[end % (PIECE_BEATS * 4)] = "Tham"
        # mridangam doubles the melodic mora stroke for stroke, landing on samam
        last_av = range((N_AV - 1) * AV_BEATS * 4, N_AV * AV_BEATS * 4)
        for k in last_av:
            grid.pop(k, None)
        c = 0
        for n in mel[:len(mel) // reps]:
            k = int(round(n["beat"] * 4))
            if n["sec"] == "mora":                                   # same stroke for the same note of each repeat
                if n["beats"] >= 1:
                    grid[k] = "Tham"; c = 0
                else:
                    grid[k] = ["Ta", "Thi", "Thom", "Num"][c % 4]; c += 1
            if n["sec"] == "ending" and n["av"] == N_AV - 1:
                grid[k] = "Tham" if n["idx"] == 0 else ("Ta" if n["idx"] == 2 else "Thi")
        mora_av = [a for a, (s, _) in enumerate(FORM) if s == "mora"][0]
        grid[(mora_av + 1) * AV_BEATS * 4] = "Tham"
        for k, s in sorted(grid.items()):
            accent = 1.0 if k % (AV_BEATS * 4) == 0 else (0.85 if k % 4 == 0 else 0.62)
            ev.append((r * piece_s + k * ak + rng.gauss(0, 0.004), s, accent * rng.uniform(0.88, 1.0)))
    return ev


def render_mridangam(md, ev, rng):
    out = np.zeros((int(FILE_S * SR), 2))
    for t, s, g in ev:
        add(out, int(max(0.0, t) * SR), rng.choice(md.s[s]) * g * STROKE_GAIN[s])
    return out


# ---------------- tanpura ----------------
def tanpura_loop(path):
    y, sr = sf.read(path, always_2d=True); assert sr == SR
    y = y[3 * SR: len(y) - 3 * SR]
    xf = int(1.5 * SR); N = int(FILE_S * SR)
    fade = np.sin(np.linspace(0, np.pi / 2, xf))[:, None]
    out = y.copy()
    while len(out) < N + xf:
        out = np.concatenate([out[:-xf], out[-xf:] * fade[::-1] + y[:xf] * fade, y[xf:]])
    head = out[:xf] * fade + out[N:N + xf] * fade[::-1]             # seamless wrap
    out = out[:N].copy(); out[:xf] = head
    return out


# ---------------- Western backing (GeneralUser GS via FluidSynth) ----------------
CHORDS = {"I": [51, 55, 58], "vi": [48, 51, 55], "IIsus4": [53, 58, 60], "Vsus2": [46, 48, 53]}
ROOT = {"I": 39, "vi": 36, "IIsus4": 41, "Vsus2": 34}
PROG = {"pallavi": ["I", "vi", "IIsus4", "Vsus2"], "anupallavi": ["vi", "I", "Vsus2", "IIsus4"],
        "swaram": ["I", "Vsus2", "vi", "IIsus4"], "mora": ["I", "Vsus2", "vi", "IIsus4"],
        "charanam": ["vi", "IIsus4", "I", "Vsus2"], "ending": ["IIsus4", "Vsus2", "I", "I"]}
DRUM_STYLE = {"pallavi": "light", "anupallavi": "ride", "swaram": "busy", "mora": "busy", "charanam": "groove", "ending": "light"}


def western_backing(spb, reps):
    rng = random.Random(17); lh, cello, drums = [], [], []
    piece_s = PIECE_BEATS * spb

    def hit(t, note, vel, ln=0.3):
        drums.append((t, t + ln, note, int(min(127, max(15, vel + rng.randint(-6, 6))))))

    for r in range(reps):
        for a, (sec, _) in enumerate(FORM):
            for half in range(2):                                      # two 4/4 bars per avartanam
                ch = PROG[sec][(a % 2) * 2 + half] if not (a == N_AV - 1 and half == 1) else "I"
                t0 = r * piece_s + (a * AV_BEATS + half * 4) * spb
                tones = CHORDS[ch]
                for e, o in enumerate([0, 1, 2, 1, 3, 1, 2, 1]):
                    p = tones[o % 3] + (12 if o >= 3 else 0); t = t0 + e * spb / 2
                    lh.append((t, t + spb / 2 + 0.05, p, 44 + (6 if e % 4 == 0 else 0) + rng.randint(-4, 4)))
                cello.append((t0, t0 + 4 * spb - 0.05, ROOT[ch] + 12, 70 + rng.randint(-5, 5)))
                style = DRUM_STYLE[sec]; bar = a * 2 + half
                fill = a % 4 == 3 and half == 1
                if half == 0 and a % 4 == 0:
                    hit(t0, 49, 88, 2.0)
                for e in range(8):
                    t = t0 + e * spb / 2; beat = e / 2
                    if fill and e >= 4:
                        hit(t, [50, 48, 47, 45][e - 4], 86); continue
                    if style == "ride":
                        hit(t, 51, 64 if e % 2 == 0 else 52)
                    elif style == "busy":
                        hit(t, 42, 64 if e % 2 == 0 else 48); hit(t + spb / 4, 42, 36)
                    else:
                        hit(t, 42, (56 if e % 2 == 0 else 42) - (6 if style == "light" else 0))
                    if beat in (0, 2) or (style in ("ride", "busy") and e == 3):
                        hit(t, 36, 92)
                    if beat in (1, 3):
                        hit(t, 37 if style == "light" else 38, 66 if style == "light" else 78)
    return (lh, []), (cello, []), (drums, [])


def fix_overlaps(notes):
    by = {}
    for n in sorted(notes):
        by.setdefault(n[2], []).append(list(n))
    out = []
    for lst in by.values():
        for a, b in zip(lst, lst[1:]):
            a[1] = min(a[1], b[0] - 0.004)
        out += [tuple(x) for x in lst if x[1] > x[0]]
    return out


def write_midi(path, tracks, bpm, end_s):
    """tracks: list of (name, program, channel, notes[(on, off, pitch, vel)])."""
    mid = mido.MidiFile(type=1, ticks_per_beat=480)
    meta = mido.MidiTrack(); meta.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(bpm), time=0))
    mid.tracks.append(meta)
    tick = lambda t: max(0, round(t * bpm / 60 * 480))
    for name, prog, ch, notes in tracks:
        tr = mido.MidiTrack(); tr.append(mido.MetaMessage("track_name", name=name, time=0))
        if prog is not None:
            tr.append(mido.Message("program_change", program=prog, channel=ch, time=0))
        ev = []
        for on, off, p, v in fix_overlaps(notes):
            ev.append((tick(on), 2, mido.Message("note_on", note=p, velocity=int(v))))
            ev.append((tick(off), 0, mido.Message("note_off", note=p, velocity=0)))
        ev.append((tick(end_s), 3, mido.Message("control_change", control=7, value=100)))
        ev.sort(key=lambda e: (e[0], e[1])); last = 0
        for tk, _, m in ev:
            tr.append(m.copy(channel=ch, time=tk - last)); last = tk
        mid.tracks.append(tr)
    mid.save(path)


def render_gm(fs_exe, sf2, name, prog, ch, notes, bpm, tmp):
    """Render three back-to-back copies, keep the middle one (seamless loop)."""
    copies = [(a + i * FILE_S, b + i * FILE_S, p, v) for i in range(3) for a, b, p, v in notes]
    mpath, wpath = os.path.join(tmp, "stem.mid"), os.path.join(tmp, "stem.wav")
    write_midi(mpath, [(name, prog, ch, copies)], bpm, 3 * FILE_S)
    subprocess.run([os.path.abspath(fs_exe), "-ni", "-q", "-g", "0.4", "-r", str(SR), "-F", wpath, sf2, mpath],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    y, sr = sf.read(wpath, always_2d=True); assert sr == SR
    y = np.pad(y, ((0, max(0, int(3 * FILE_S * SR) - len(y))), (0, 0)))
    return y[int(FILE_S * SR): int(2 * FILE_S * SR)]


# ---------------- notation export for the reviewer ----------------
def write_notation(path):
    lines = ["Raga Mohanam, Adi talam (8 beats). Sa = Eb. Numbers = beats; '~' = kampita; '_' lower octave, '^' upper.",
             "Gamakas applied automatically in the Indian-style render: jaru into every note; Sa/Pa plain;",
             "Dha ascending 'pa-sa-dha', descending 'sa-dha'; Ga descending 'pa-ga'; Ri descending 'ga-ri';",
             "kampita (to the upper swara) where marked '~' and on some long Ri/Ga/Dha; sphuritam on repeated notes.", ""]
    for a, (sec, av) in enumerate(FORM):
        lines.append(f"{a + 1:2d}  {sec:<10s}  {av}")
    open(path, "w", encoding="utf8").write("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--assets", required=True); ap.add_argument("--fluidsynth", required=True); ap.add_argument("--gm", required=True)
    a = ap.parse_args()
    out_dir, midi_dir = os.path.join(HERE, "stimuli"), os.path.join(HERE, "midi")
    os.makedirs(out_dir, exist_ok=True); os.makedirs(midi_dir, exist_ok=True)
    vln = Violin(os.path.join(a.assets, "violin")); md = Mridangam(os.path.join(a.assets, "mridangam"))
    tan = tanpura_loop(os.path.join(a.assets, "tanpura_Eb.mp3"))
    notes = compose(); mixes = {}
    norm = lambda y: y / (np.sqrt(np.mean(y ** 2)) + 1e-12)
    with tempfile.TemporaryDirectory() as tmp:
        for tag, bpm in (("slow", 60), ("fast", 120)):
            spb = 60 / bpm; reps = int(round(FILE_S / (PIECE_BEATS * spb)))
            mel = timed(notes, spb, reps)
            v_ind = violin_line(vln, mel, "indian", random.Random(5)); print(f"  {tag}: violin (Indian style)")
            v_wes = violin_line(vln, mel, "western", random.Random(5)); print(f"  {tag}: violin (Western style)")
            rng = random.Random(13)
            mr = render_mridangam(md, mridangam_events(mel, spb, reps, rng), rng); print(f"  {tag}: mridangam")
            (lh, _), (ce, _), (dr, _) = western_backing(spb, reps)
            piano = render_gm(a.fluidsynth, a.gm, "piano", 0, 0, lh, bpm, tmp)
            cello = render_gm(a.fluidsynth, a.gm, "cello", 42, 0, ce, bpm, tmp)
            drums = render_gm(a.fluidsynth, a.gm, "drums", None, 9, dr, bpm, tmp); print(f"  {tag}: western backing")
            mixes["A_raga_slow" if tag == "slow" else "B_raga_fast"] = norm(v_ind) + 0.33 * norm(tan) + 0.7 * norm(mr)
            mixes["C_western_slow" if tag == "slow" else "D_western_fast"] = norm(v_wes) + 0.45 * norm(piano) + 0.4 * norm(cello) + 0.45 * norm(drums)
            piece_s = PIECE_BEATS * spb
            one = [n for n in mel if n["on"] < piece_s]
            vnotes = [(n["on"], n["on"] + n["dur"], pitch(n["idx"]), n["vel"]) for n in one]
            write_midi(os.path.join(midi_dir, f"mohanam_{tag}.mid"),
                       [("Violin (melody, plain; gamakas are added at render time)", 40, 0, vnotes),
                        ("Piano left hand (Western style)", 0, 1, [x for x in lh if x[0] < piece_s]),
                        ("Cello (Western style)", 42, 2, [x for x in ce if x[0] < piece_s]),
                        ("Drums (Western style)", None, 9, [x for x in dr if x[0] < piece_s])], bpm, piece_s)
    write_notation(os.path.join(midi_dir, "mohanam_notation.txt"))
    rms = {k: np.sqrt(np.mean(v ** 2)) for k, v in mixes.items()}
    target = min(0.1, *[0.89 / np.abs(v).max() * rms[k] for k, v in mixes.items()])
    for k, v in sorted(mixes.items()):
        y = v * (target / rms[k])
        sf.write(os.path.join(out_dir, k + ".mp3"), y, SR, format="MP3")
        print(f"{k}.mp3 rms={20*np.log10(np.sqrt(np.mean(y**2))):.1f} dBFS peak={20*np.log10(np.abs(y).max()):.1f} dBFS")


if __name__ == "__main__":
    main()
