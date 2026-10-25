"""Build the real-recording stimuli: cut a source stretch, time-stretch it to a target pulse with Rubber Band
(pitch unchanged), make it loop seamlessly (2 s crossfade of tail into head), match loudness, write MP3.

Usage: python make_real_stimuli.py OUT_DIR
Sources: veena concert (Ramana Balachandhran, "Emi Neramu", Shankarabharanam, YouTube aJsywTs7Vuk),
Kevin MacLeod "Almost Bliss" and "Bossa Antigua" (incompetech.com, CC BY 4.0).
The source audio is not in this repo: put concert.wav (yt-dlp audio of the video) next to this script and the two
MP3s in western/. Output in this repo: stimuli/candidates/."""
import os
import subprocess
import sys

import imageio_ffmpeg
import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
FF = imageio_ffmpeg.get_ffmpeg_exe()
SR = 44100
SLOW, FAST = 60.0, 100.0          # target pulse in BPM
TARGET_RMS_DB = -20.0
XFADE_S = 2.0

# name -> (source file, start s, duration s, measured original pulse BPM)
SOURCES = {
    "veena":   (os.path.join(HERE, "concert.wav"), 1390, 280, 78.3),
    "bliss":   (os.path.join(HERE, "western", "Almost Bliss.mp3"), 0, 317, 89.1),
    "antigua": (os.path.join(HERE, "western", "Bossa Antigua.mp3"), 0, 283, 92.3),
}


def stretch(src, start, dur, factor, tmp):
    """Cut [start, start+dur) and change its tempo by `factor` (>1 = faster) without changing pitch."""
    cmd = [FF, "-v", "error", "-y", "-ss", str(start), "-t", str(dur), "-i", src,
           "-af", f"rubberband=tempo={factor:.5f}:transients=crisp:detector=percussive:window=standard",
           "-ar", str(SR), "-ac", "2", tmp]
    subprocess.run(cmd, check=True)
    y, _ = sf.read(tmp, dtype="float32")
    return y


def make_loop(y):
    n = int(XFADE_S * SR)
    ramp = np.linspace(0, 1, n, dtype=np.float32)[:, None]
    out = y[:-n].copy()
    out[:n] = y[:n] * ramp + y[-n:] * (1 - ramp)       # the tail flows into the head when the file repeats
    return out


def normalise(y):
    y = y * (10 ** (TARGET_RMS_DB / 20) / np.sqrt(np.mean(y ** 2)))
    peak = np.abs(y).max()
    if peak > 0.98:                                     # soft-limit rare peaks instead of clipping
        y = np.tanh(y / 0.98) * 0.98
    return y


def main():
    out_dir = sys.argv[1]
    os.makedirs(out_dir, exist_ok=True)
    tmp = os.path.join(out_dir, "_tmp.wav")
    for name, (src, start, dur, bpm) in SOURCES.items():
        for label, target in (("slow", SLOW), ("fast", FAST)):
            f = target / bpm
            y = normalise(make_loop(stretch(src, start, dur, f, tmp)))
            path = os.path.join(out_dir, f"{name}_{label}.mp3")
            sf.write(path, y, SR, format="MP3")
            print(f"{name}_{label}.mp3  x{f:.2f}  {bpm:.0f}->{target:.0f} BPM  {len(y)/SR/60:.1f} min")
    os.remove(tmp)


if __name__ == "__main__":
    main()
