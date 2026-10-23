"""Make fake data in exactly the website's CSV format, to test analyze.py (and for power checks).

Usage:
    python simulate.py OUT_DIR [--n 40] [--seed 1] [--music -0.25] [--style 0.15] [--tempo -0.10] [--style-fam 0.0]

Effects are in log-odds of recalling a digit in position:
  --music      any music vs quiet (negative = irrelevant-sound cost)
  --style      Indian style minus Western style
  --tempo      fast minus slow
  --style-fam  extra Indian-style effect per SD of Carnatic familiarity (cultural account)
Also writes, on purpose: one test run, one unfinished session (progress files only), one
session with a resume, and one participant who pressed "Start over" (duplicate ID).
"""
import argparse, os, random
import numpy as np
import pandas as pd

ORDERS = ["ABECD", "BCADE", "CDBEA", "DECAB", "EADBC", "DCEBA", "EDACB", "AEBDC", "BACED", "CBDAE"]
COND = {"A": ("raga", "slow"), "B": ("raga", "fast"), "C": ("western", "slow"), "D": ("western", "fast"), "E": ("quiet", "none")}
POS_CURVE = np.array([0.9, 0.5, 0.1, -0.2, -0.4, -0.5, -0.5, -0.3, 0.1])   # primacy and a small recency bump (9 positions)


def session(pid, sid, row, rng, eff, fam, base, blocks=5, test=0, resume_at=None):
    rows = []
    order = ORDERS[row]
    famz = (fam - 3) / 1.2
    for b in range(blocks):
        cond = order[b]; style, tempo = COND[cond]
        logit = base + 0.08 * (b - 2)                                   # small practice effect
        if style != "quiet":
            logit += eff["music"]
            s = 0.5 if style == "raga" else -0.5
            logit += s * (eff["style"] + eff["style_fam"] * famz) + (0.5 if tempo == "fast" else -0.5) * eff["tempo"]
        resumes = 1 if resume_at is not None and b >= resume_at else 0
        for k in range(8):
            stim = rng.sample(range(1, 10), 9)
            resp = [str(x) if rng.random() < 1 / (1 + np.exp(-(logit + POS_CURVE[i]))) else "-" for i, x in enumerate(stim)]
            hits = sum(r == str(x) for r, x in zip(resp, stim))
            rows.append(dict(participant=pid, session_id=sid, test_run=test, order_row=row + 1, order=order, order_source="datapipe",
                             resumes=resumes, fam_carnatic=fam, fam_hindustani=2, training_years=0, audio_ok=True,
                             timestamp=f"2026-11-01T10:{b:02d}:{k:02d}Z", block_position=b + 1, condition=cond, style=style,
                             tempo=tempo, task="recall", trial=k + 1, list_length=9, stimulus="".join(map(str, stim)),
                             response="".join(resp), n_correct_positions=hits, correct=int(hits == 9), rt_ms=6000, tab_hidden_so_far=0))
        ratings = [("alertness", 3), ("mood", 3)] + ([("indian", 4 if style == "raga" else 2)] if style != "quiet" else [])
        for name, v in ratings:
            rows.append(dict(participant=pid, session_id=sid, test_run=test, order_row=row + 1, order=order, order_source="datapipe",
                             resumes=resumes, fam_carnatic=fam, fam_hindustani=2, training_years=0, audio_ok=True,
                             timestamp=f"2026-11-01T10:{b:02d}:59Z", block_position=b + 1, condition=cond, style=style, tempo=tempo,
                             task="rating", stimulus=name, response=max(1, min(5, v + rng.choice([-1, 0, 0, 1])))))
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out"); ap.add_argument("--n", type=int, default=40); ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--music", type=float, default=-0.25); ap.add_argument("--style", type=float, default=0.15)
    ap.add_argument("--tempo", type=float, default=-0.10); ap.add_argument("--style-fam", type=float, default=0.0)
    a = ap.parse_args()
    eff = {"music": a.music, "style": a.style, "tempo": a.tempo, "style_fam": a.style_fam}
    rng = random.Random(a.seed); nrng = np.random.default_rng(a.seed)
    os.makedirs(a.out, exist_ok=True)
    def write(df, name): df.to_csv(os.path.join(a.out, name), index=False)
    for i in range(a.n):
        pid, sid = f"P{i:03d}", f"s{i:07d}"
        df = session(pid, sid, i % 10, rng, eff, fam=int(nrng.integers(1, 6)), base=nrng.normal(0.4, 0.6),
                     resume_at=2 if i == 3 else None)
        for b in range(1, 6):                                            # progress files, as the site uploads them
            write(df[df["block_position"] <= b], f"{pid}_{sid}_progress_b{b}.csv")
        write(df, f"{pid}_{sid}_trials.csv")
    # an unfinished session: 3 blocks, progress files only
    df = session("P900", "sunfinsh", 3, rng, eff, fam=4, base=0.3, blocks=3)
    for b in range(1, 4): write(df[df["block_position"] <= b], f"P900_sunfinsh_progress_b{b}.csv")
    # a test run that must be excluded
    write(session("BOT", "stestrun", 0, rng, eff, fam=3, base=2, test=1), "TEST_BOT_stestrun_trials.csv")
    # "Start over": same ID, an abandoned first session with 1 block
    df = session("P000", "sabandon", 5, rng, eff, fam=2, base=0.3, blocks=1)
    write(df, "P000_sabandon_progress_b1.csv")
    print(f"wrote fake data for {a.n} complete + 1 unfinished + 1 test + 1 duplicate-ID session to {a.out}")


if __name__ == "__main__":
    main()
