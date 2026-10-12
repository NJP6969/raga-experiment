"""Synthesize the four music stimuli for the experiment (Quiet needs no file).

Same melody (Bhupali pitch set: S R G P D = C D E G A) in every file.
  Raga:    bansuri-like tone with glides (meend), oscillation (andolan) on G, tanpura drone.
  Western: plain plucked-piano-like tone, discrete pitches, no ornaments, no drone.
  Slow = 60 BPM, fast = 120 BPM (same phrases, faster).
All files are RMS-matched. Usage: python make_stimuli.py   (needs numpy)
"""
import os, wave
import numpy as np

SR = 22050
DUR = 240.0                      # seconds; the page loops the file
SA = 261.63                      # C4
OFF = {"S": 0, "R": 2, "G": 4, "P": 7, "D": 9, "S^": 12, "D_": -3}
PHRASES = [
    "S1 R1 G2 P2 G1 R1 S2",
    "G1 P1 D1 P1 G2 R1 G1 S2",
    "P1 G1 D1 P1 G1 R1 S2",
    "D_1 S1 R1 G2 R1 S1 D_2",
    "G1 P1 D1 S^2 D1 P1 G2 R1 S2",
    "S^1 D1 P1 G1 P1 D1 S^2",
    "R1 G1 P1 D1 P1 G1 R1 S2",
]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stimuli")


def events(seed=7):
    """Fixed note list [(semitone offset, beats)], with a 2-beat rest between phrases."""
    rng = np.random.default_rng(seed)
    ev, last = [], -1
    for _ in range(80):
        i = int(rng.integers(len(PHRASES)))
        if i == last:
            i = (i + 1) % len(PHRASES)
        last = i
        for tok in PHRASES[i].split():
            name, beats = tok[:-1], int(tok[-1])
            ev.append((OFF[name], float(beats)))
        ev.append((None, 2.0))
    return ev


def hz(semi):
    return SA * 2 ** (semi / 12)


def render_flute(ev, bpm, total):
    out = np.zeros(int(total * SR) + SR)
    rng = np.random.default_rng(1)
    t0, prev = 0.0, None
    for semi, beats in ev:
        dur = beats * 60 / bpm
        if semi is not None:
            n = int(dur * SR)
            t = np.arange(n) / SR
            f = np.full(n, hz(semi))
            if prev is not None:                                   # meend: glide from previous pitch
                tg = min(0.2, 0.4 * dur)
                m = t < tg
                w = 0.5 - 0.5 * np.cos(np.pi * t[m] / tg)
                f[m] = hz(prev) + (hz(semi) - hz(prev)) * w
            if semi == 4:                                          # andolan on G
                ramp = np.clip((t - 0.35 * dur) / (0.2 * dur + 1e-9), 0, 1)
                f = f * 2 ** (35 * ramp * np.sin(2 * np.pi * 5.5 * t) / 1200)
            ph = 2 * np.pi * np.cumsum(f) / SR
            sig = sum(a * np.sin(k * ph) for k, a in enumerate([1, .45, .22, .10, .05], 1))
            noise = np.convolve(rng.standard_normal(n), np.ones(8) / 8, "same") * 0.05
            sig = sig + noise
            att, rel = int(0.03 * SR), int(0.08 * SR)
            env = np.ones(n)
            env[:att] = np.linspace(0, 1, att)
            env[-rel:] *= np.linspace(1, 0, rel)
            i0 = int(t0 * SR)
            if i0 + n < len(out):
                out[i0:i0 + n] += sig * env
            prev = semi
        t0 += dur
        if t0 >= total:
            break
    return out


def render_piano(ev, bpm, total):
    out = np.zeros(int(total * SR) + 3 * SR)
    t0 = 0.0
    for semi, beats in ev:
        dur = beats * 60 / bpm
        if semi is not None:
            ln = min(dur + 0.3, 2.5)
            n = int(ln * SR)
            t = np.arange(n) / SR
            f = hz(semi)
            sig = sum(a * np.sin(2 * np.pi * k * f * t) for k, a in enumerate([1, .6, .35, .2, .12, .07], 1))
            env = np.exp(-t / 0.9)
            att = int(0.004 * SR)
            env[:att] *= np.linspace(0, 1, att)
            rel = int(0.06 * SR)
            env[-rel:] *= np.linspace(1, 0, rel)
            i0 = int(t0 * SR)
            if i0 + n < len(out):
                out[i0:i0 + n] += sig * env
        t0 += dur
        if t0 >= total:
            break
    return out


def pluck(freq, length=4.0):
    t = np.arange(int(length * SR)) / SR
    sig = np.zeros_like(t)
    for k in range(1, 21):
        if freq * k > 9000:
            break
        amp = (1 / k ** 0.8) * (1 + 1.6 * np.exp(-((k - 6) / 3.0) ** 2))   # jivari-like brightness
        sig += amp * np.sin(2 * np.pi * k * freq * t) * np.exp(-t / (2.5 / k ** 0.5))
    sig[:int(0.003 * SR)] *= np.linspace(0, 1, int(0.003 * SR))
    return sig


def render_drone(bpm, total):
    strings = [pluck(SA * 0.75), pluck(SA), pluck(SA), pluck(SA / 2)]      # Pa, Sa, Sa, low Sa
    out = np.zeros(int(total * SR) + 5 * SR)
    step = 60 / bpm
    i, t = 0, 0.0
    while t < total:
        s = strings[i % 4]
        i0 = int(t * SR)
        out[i0:i0 + len(s)] += s
        t += step
        i += 1
    return out


def finish(x, total):
    x = x[:int(total * SR)].copy()
    x -= x.mean()
    f = int(0.05 * SR)
    x[:f] *= np.linspace(0, 1, f)
    x[-f:] *= np.linspace(1, 0, f)
    return x


def main():
    os.makedirs(OUT, exist_ok=True)
    ev = events()
    tracks = {}
    for tag, bpm in (("slow", 60), ("fast", 120)):
        flute = finish(render_flute(ev, bpm, DUR), DUR)
        drone = finish(render_drone(bpm, DUR), DUR)
        piano = finish(render_piano(ev, bpm, DUR), DUR)
        flute /= np.abs(flute).max(); drone /= np.abs(drone).max(); piano /= np.abs(piano).max()
        tracks["A_raga_slow" if tag == "slow" else "B_raga_fast"] = flute + 0.5 * drone
        tracks["C_western_slow" if tag == "slow" else "D_western_fast"] = piano
    rms = {k: np.sqrt(np.mean(v ** 2)) for k, v in tracks.items()}
    peak = {k: np.abs(v).max() for k, v in tracks.items()}
    target = min(0.1, *[0.95 / peak[k] * rms[k] for k in tracks])           # common RMS, no clipping
    for k, v in sorted(tracks.items()):
        y = v * (target / rms[k])
        pcm = (np.clip(y, -1, 1) * 32767).astype("<i2")
        path = os.path.join(OUT, k + ".wav")
        with wave.open(path, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
        print(f"{k}.wav  {len(pcm)/SR:.0f}s  rms={20*np.log10(np.sqrt(np.mean(y**2))):.1f} dBFS  peak={20*np.log10(np.abs(y).max()):.1f} dBFS")


if __name__ == "__main__":
    main()
