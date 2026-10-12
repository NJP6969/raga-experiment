"""Synthesize the four music stimuli for the experiment (Quiet needs no file).

One composed 64-beat form (four 16-beat cycles) in the Bhupali pitch set (S R G P D = C D E G A),
continuous with no rests, repeated and looping seamlessly.
  Raga:    bansuri-like melody (meend glides, andolan on G) + tanpura drone + tabla teentaal theka.
  Western: plain piano-like melody (same notes and timing, no ornaments) + soft pentatonic chord bed
           + kick/snare/hi-hat in 4/4.
Slow = 60 BPM, fast = 120 BPM. Length 256 s = whole number of cycles at both tempos, so the loop is
seamless. All files are RMS-matched.  Usage: python make_stimuli.py   (needs numpy)
"""
import os, re, wave
import numpy as np

SR = 22050
DUR = 256.0
SA = 261.63                      # C4
OFF = {"S": 0, "R": 2, "G": 4, "P": 7, "D": 9, "S^": 12, "D_": -3}
FORM = [                         # four 16-beat cycles, each sums to 16 beats
    "S1 R1 G2 P2 G1 R1 S1 D_1 S2 R1 G1 P1 G1",
    "G1 P1 D2 P1 G1 R1 G1 P2 G1 R1 S2 R1 G1",
    "P1 D1 S^2 D1 P1 G2 P1 D1 S^1 D1 P1 G1 R1 G1",
    "S^2 D1 P1 G1 P1 D1 P1 G1 R1 G2 R1 S1 D_1 S1",
]
CHORDS = [[-12, -5, 4], [-15, -8, 0], [-12, -10, -5], [-17, -10, -3]]   # C, Am, Csus2, Gsus2 (pentatonic only)
THEKA = ["dha", "dhin", "dhin", "dha", "dha", "dhin", "dhin", "dha",
         "dha", "tin", "tin", "ta", "ta", "dhin", "dhin", "dha"]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stimuli")
RNG = np.random.default_rng(3)


def melody():
    ev = []
    for cyc in FORM:
        tot = 0
        for tok in cyc.split():
            m = re.fullmatch(r"(S\^|D_|S|R|G|P|D)([\d.]+)", tok)
            ev.append((OFF[m.group(1)], float(m.group(2)))); tot += float(m.group(2))
        assert tot == 16, (cyc, tot)
    return ev


def hz(semi):
    return SA * 2 ** (semi / 12)


def add(buf, i0, sig):
    """Add sig at i0, wrapping around the end so the loop is seamless."""
    N = len(buf); i0 %= N; e = i0 + len(sig)
    if e <= N:
        buf[i0:e] += sig
    else:
        k = N - i0; buf[i0:] += sig[:k]; buf[:len(sig) - k] += sig[k:]


def env_ar(n, att, rel):
    e = np.ones(n); a, r = min(int(att * SR), n), min(int(rel * SR), n)
    e[:a] = np.linspace(0, 1, a); e[n - r:] *= np.linspace(1, 0, r)
    return e


def flute(ev, bpm, N):
    out = np.zeros(N); t0 = 0.0; prev = ev[-1][0]
    nbeats = DUR * bpm / 60
    reps = int(nbeats // sum(b for _, b in ev))
    for _ in range(reps):
        for semi, beats in ev:
            dur = beats * 60 / bpm
            n = int((dur + 0.08) * SR); t = np.arange(n) / SR
            f = np.full(n, hz(semi))
            tg = min(0.2, 0.4 * dur)
            if prev != semi:                                       # meend from previous pitch
                m = t < tg
                f[m] = hz(prev) + (hz(semi) - hz(prev)) * (0.5 - 0.5 * np.cos(np.pi * t[m] / tg))
            if semi == 4:                                          # andolan on G
                ramp = np.clip((t - 0.35 * dur) / (0.2 * dur + 1e-9), 0, 1)
                f = f * 2 ** (35 * ramp * np.sin(2 * np.pi * 5.5 * t) / 1200)
            ph = 2 * np.pi * np.cumsum(f) / SR
            sig = sum(a * np.sin(k * ph) for k, a in enumerate([1, .45, .22, .10, .05], 1))
            sig = sig + np.convolve(RNG.standard_normal(n), np.ones(8) / 8, "same") * 0.05
            add(out, int(t0 * SR), sig * env_ar(n, 0.03, 0.08))
            prev = semi; t0 += dur
    return out


def piano(ev, bpm, N):
    out = np.zeros(N); t0 = 0.0
    reps = int((DUR * bpm / 60) // sum(b for _, b in ev))
    for _ in range(reps):
        for semi, beats in ev:
            dur = beats * 60 / bpm
            n = int(min(dur + 0.8, 3.0) * SR); t = np.arange(n) / SR
            sig = sum(a * np.sin(2 * np.pi * k * hz(semi) * t) for k, a in enumerate([1, .6, .35, .2, .12, .07], 1))
            env = np.exp(-t / 1.2) * env_ar(n, 0.004, 0.08)
            add(out, int(t0 * SR), sig * env)
            t0 += dur
    return out


def pad(bpm, N):
    out = np.zeros(N); dur = 4 * 60 / bpm; i = 0; t0 = 0.0
    while t0 < DUR - 1e-6:
        n = int((dur + 0.5) * SR); t = np.arange(n) / SR
        sig = sum(np.sin(2 * np.pi * hz(s) * t) + 0.3 * np.sin(4 * np.pi * hz(s) * t) for s in CHORDS[i % 4])
        add(out, int(t0 * SR), sig * env_ar(n, 0.3, 0.5)); t0 += dur; i += 1
    return out


def pluck(freq, length=4.0):
    t = np.arange(int(length * SR)) / SR; sig = np.zeros_like(t)
    for k in range(1, 21):
        if freq * k > 9000:
            break
        amp = (1 / k ** 0.8) * (1 + 1.6 * np.exp(-((k - 6) / 3.0) ** 2))   # jivari-like brightness
        sig += amp * np.sin(2 * np.pi * k * freq * t) * np.exp(-t / (2.5 / k ** 0.5))
    sig[:int(0.003 * SR)] *= np.linspace(0, 1, int(0.003 * SR))
    return sig


def drone(bpm, N):
    strings = [pluck(SA * 0.75), pluck(SA), pluck(SA), pluck(SA / 2)]
    out = np.zeros(N); step = 60 / bpm
    for i in range(int(DUR / step)):
        add(out, int(i * step * SR), strings[i % 4])
    return out


# ---- percussion ----
def _t(d): return np.arange(int(d * SR)) / SR
def noise(n): return RNG.standard_normal(n)

def bayan():
    t = _t(0.5); f = 80 + 50 * np.exp(-t / 0.08)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.18)

def dayan(tau):
    t = _t(0.5); tone = sum(a * np.sin(2 * np.pi * SA * k * t) for k, a in zip((1, 2, 3), (1, .6, .35)))
    click = np.convolve(noise(len(t)), [1, -1], "same") * np.exp(-t / 0.004) * 0.5
    return tone * np.exp(-t / tau) + click

def kick():
    t = _t(0.35); f = 45 + 75 * np.exp(-t / 0.03)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.1)

def snare():
    t = _t(0.25)
    return 0.7 * np.convolve(noise(len(t)), [1, -1], "same") * np.exp(-t / 0.05) + 0.5 * np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.04)

def hat():
    t = _t(0.08)
    return np.convolve(noise(len(t)), [1, -2, 1], "same") * np.exp(-t / 0.015) * 0.4


def tabla(bpm, N):
    out = np.zeros(N); step = 60 / bpm
    ge, ring, damp = bayan(), dayan(0.35), dayan(0.06)
    for i in range(int(DUR / step)):
        bol = THEKA[i % 16]; i0 = int(i * step * SR)
        if bol in ("dha", "dhin"): add(out, i0, 0.8 * ge)
        add(out, i0, 0.6 * (ring if bol in ("dha", "dhin", "tin") else damp))
        add(out, i0 + int(0.5 * step * SR), 0.18 * damp)                # soft off-beat tap
    return out


def drums(bpm, N):
    out = np.zeros(N); step = 60 / bpm; k, s, h = kick(), snare(), hat()
    for i in range(int(DUR / step)):
        i0 = int(i * step * SR)
        add(out, i0, 0.9 * (k if i % 2 == 0 else s))
        add(out, i0, h); add(out, i0 + int(0.5 * step * SR), 0.7 * h)
    return out


def fin(x):
    x = x - x.mean(); return x / np.abs(x).max()


def main():
    os.makedirs(OUT, exist_ok=True)
    N = int(DUR * SR); ev = melody(); tracks = {}
    for tag, bpm in (("slow", 60), ("fast", 120)):
        raga = fin(flute(ev, bpm, N)) + 0.4 * fin(drone(bpm, N)) + 0.7 * fin(tabla(bpm, N))
        west = fin(piano(ev, bpm, N)) + 0.35 * fin(pad(bpm, N)) + 0.6 * fin(drums(bpm, N))
        tracks["A_raga_slow" if tag == "slow" else "B_raga_fast"] = raga
        tracks["C_western_slow" if tag == "slow" else "D_western_fast"] = west
    rms = {k: np.sqrt(np.mean(v ** 2)) for k, v in tracks.items()}
    peak = {k: np.abs(v).max() for k, v in tracks.items()}
    target = min(0.1, *[0.95 / peak[k] * rms[k] for k in tracks])
    for k, v in sorted(tracks.items()):
        y = v * (target / rms[k]); pcm = (np.clip(y, -1, 1) * 32767).astype("<i2")
        with wave.open(os.path.join(OUT, k + ".wav"), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
        win = y[:len(y) // (SR // 4) * (SR // 4)].reshape(-1, SR // 4)          # 250 ms windows
        wr = 20 * np.log10(np.sqrt((win ** 2).mean(1)) + 1e-9)
        seam = abs(float(y[0] - y[-1]))
        print(f"{k}.wav {len(pcm)/SR:.0f}s rms={20*np.log10(np.sqrt(np.mean(y**2))):.1f} peak={20*np.log10(np.abs(y).max()):.1f} dBFS "
              f"quietest 250ms={wr.min():.1f} dBFS (median {np.median(wr):.1f}) loop-seam jump={seam:.4f}")


if __name__ == "__main__":
    main()
