"""Pre-registered analysis for the music & memory experiment.

Usage:
    python analyze.py DATA_DIR [--out results] [--keep-duplicate-ids]

DATA_DIR is the downloaded DataPipe / Google Drive folder (searched recursively for *.csv).

Steps (in this order, all reported in results/summary.txt):
 1. File selection, per session_id: the final <ID>_<session>_trials.csv if present, otherwise the
    highest-numbered <ID>_<session>_progress_b<N>[_r<K>].csv (most completed blocks).
 2. Exclusions:
    a. test runs (test_run == 1) and pilot sessions from earlier task versions (list length != 9,
       or stimulus_set != "real-v1", i.e. the generated music used before 27 Oct 2026);
    b. music blocks where audio failed (audio_ok false) are dropped;
    c. if one participant ID has several sessions (e.g. "Start over"), keep the session with the
       most completed recall lists (earliest if tied), unless --keep-duplicate-ids;
    d. participants whose overall recall is below 0.20 (near chance for 8 of 9 digits ~ 0.11),
       treated as not doing the task. Baseline ratings (block 0) are kept out of all models.
 3. Outcome: each digit scored 1 if recalled in its correct serial position (9 per list, all of
    1-9; 8 lists per block), recomputed from stimulus and response.
 4. Models: logistic GEE at the digit level, clustered by participant (exchangeable working
    correlation, robust SEs), effect-coded predictors, block position as a centred covariate.
      H1  quiet vs music:            correct ~ music + pos_c                       (all blocks)
      H2  style x tempo:             correct ~ style_c * tempo_c + pos_c           (music blocks)
      H3  two accounts:              correct ~ style_c * famC_z + tempo_c + pos_c  (music blocks)
          segmentation account -> style_c > 0 with no style_c:famC_z interaction;
          cultural account     -> style_c:famC_z > 0.
    Robustness: linear mixed model on block-level proportions, random intercept per participant.
    Sensitivity: H2 refitted without blocks where the tab was hidden or that followed a resume.
    Manipulation check: "how Indian" rating ~ style_c + tempo_c + pos_c (linear mixed model).
    Exploratory: H2 adjusted for device (phone/touch vs computer), when both occur.
 Coding: style_c = +0.5 Indian style / -0.5 Western style; tempo_c = +0.5 fast / -0.5 slow;
 music = 1 for any music block, 0 quiet; famC_z = standardised Carnatic familiarity.
"""
import argparse, glob, os, re, sys
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

FILE_RE = re.compile(r"^(?P<base>.+?)_(?P<kind>trials|blocks|progress_b(?P<n>\d+)(?:_r(?P<r>\d+))?)\.csv$")
MIN_OVERALL = 0.20
LIST_LEN = 9          # the registered task; earlier pilot versions used 8
STIMULUS_SET = "real-v1"   # real recordings (veena, Almost Bliss); earlier pilots used generated music


def select_files(data_dir, log):
    found = {}
    for path in glob.glob(os.path.join(data_dir, "**", "*.csv"), recursive=True):
        m = FILE_RE.match(os.path.basename(path))
        if not m or m["kind"] == "blocks":
            continue
        session = m["base"].rsplit("_", 1)[-1]
        rank = (2, 0, 0) if m["kind"] == "trials" else (1, int(m["n"]), int(m["r"] or 0))
        if session not in found or rank > found[session][0]:
            found[session] = (rank, path)
    n_final = sum(1 for r, _ in found.values() if r[0] == 2)
    log(f"Sessions found: {len(found)} ({n_final} finished, {len(found) - n_final} partial: latest progress file used)")
    return [p for _, p in found.values()]


def load(paths):
    frames = []
    for p in paths:
        d = pd.read_csv(p, dtype={"stimulus": str, "response": str, "participant": str, "session_id": str})
        d["source_file"] = os.path.basename(p)
        frames.append(d)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def digit_level(recall):
    out = []
    for r in recall.itertuples(index=False):
        stim, resp = str(r.stimulus), str(r.response)
        for k, ch in enumerate(stim):
            out.append({"session_id": r.session_id, "participant": r.participant, "condition": r.condition,
                        "style": r.style, "tempo": r.tempo, "block_position": r.block_position,
                        "list": r.trial, "serial_position": k + 1,
                        "correct": int(k < len(resp) and resp[k] == ch),
                        "fam_carnatic": r.fam_carnatic, "tab_hidden": getattr(r, "tab_hidden_so_far", 0),
                        "resumes": r.resumes, "device": getattr(r, "device", "computer")})
    return pd.DataFrame(out)


def gee(formula, data, log, title):
    log(f"\n--- {title} ---\n{formula}   (n digits = {len(data)}, participants = {data['session_id'].nunique()})")
    if data["session_id"].nunique() < 2:
        log("  not enough participants to fit"); return None
    m = smf.gee(formula, groups="session_id", data=data, family=sm.families.Binomial(),
                cov_struct=sm.cov_struct.Exchangeable()).fit()
    tab = pd.DataFrame({"b (log-odds)": m.params, "SE": m.bse, "z": m.tvalues, "p": m.pvalues,
                        "OR": np.exp(m.params), "OR 2.5%": np.exp(m.conf_int()[0]), "OR 97.5%": np.exp(m.conf_int()[1])})
    log(tab.round(4).to_string())
    return tab


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data_dir"); ap.add_argument("--out", default="results")
    ap.add_argument("--keep-duplicate-ids", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    lines = []
    def log(s=""):
        print(s); lines.append(str(s))

    raw = load(select_files(a.data_dir, log))
    if raw.empty:
        log("No data files found."); return
    log(f"Rows read: {len(raw)}")

    # --- exclusions ---
    n0 = raw["session_id"].nunique()
    d = raw[raw["test_run"].astype(str).isin(["0", "0.0", "False", "false"])].copy()
    log(f"Excluded test runs: {n0 - d['session_id'].nunique()} sessions")
    rec = d[d["task"] == "recall"].copy()
    sset = rec["stimulus_set"].astype(str) if "stimulus_set" in rec else pd.Series("", index=rec.index)
    old = (rec["list_length"].astype(float) != LIST_LEN) | (sset != STIMULUS_SET)
    if old.any():
        log(f"Excluded sessions run with an earlier task version (list length != {LIST_LEN} or stimulus set != {STIMULUS_SET}, i.e. pilots): {rec.loc[old, 'session_id'].nunique()}")
    rec = rec[~old]
    bad_audio = rec["audio_ok"].astype(str).str.lower().isin(["false", "0"]) & (rec["style"] != "quiet")
    log(f"Excluded music blocks with failed audio: {rec[bad_audio].groupby(['session_id', 'block_position']).ngroups}")
    rec = rec[~bad_audio]
    if not a.keep_duplicate_ids:
        sizes = rec.groupby(["participant", "session_id"]).agg(n=("trial", "size"), t=("timestamp", "min")).reset_index()
        sizes["pid"] = sizes["participant"].str.upper()
        keep = sizes.sort_values(["pid", "n", "t"], ascending=[True, False, True]).drop_duplicates("pid")["session_id"]
        dropped = set(sizes["session_id"]) - set(keep)
        if dropped:
            log(f"Duplicate participant IDs: kept the most complete session, dropped {len(dropped)}: {sorted(dropped)}")
        rec = rec[rec["session_id"].isin(keep)]
    dig = digit_level(rec)
    if dig.empty:
        log("\nFINAL SAMPLE: 0 participants (nothing left after exclusions).")
        open(os.path.join(a.out, "summary.txt"), "w", encoding="utf8").write("\n".join(lines) + "\n"); return
    overall = dig.groupby("session_id")["correct"].mean()
    low = overall[overall < MIN_OVERALL].index
    log(f"Excluded participants with overall recall < {MIN_OVERALL}: {len(low)}")
    dig = dig[~dig["session_id"].isin(low)].copy()
    n_part = dig["session_id"].nunique()
    log(f"\nFINAL SAMPLE: {n_part} participants, {dig.groupby(['session_id', 'block_position']).ngroups} blocks, {len(dig)} digits")
    if n_part == 0:
        return

    # --- coding ---
    dig["music"] = (dig["style"] != "quiet").astype(int)
    dig["style_c"] = dig["style"].map({"raga": 0.5, "western": -0.5, "quiet": 0.0})
    dig["tempo_c"] = dig["tempo"].map({"fast": 0.5, "slow": -0.5, "none": 0.0})
    dig["pos_c"] = dig["block_position"] - 3
    fam = dig.drop_duplicates("session_id").set_index("session_id")["fam_carnatic"].astype(float)
    sd = fam.std(ddof=0)
    dig["famC_z"] = dig["session_id"].map((fam - fam.mean()) / (sd if sd > 0 else 1))
    dig.to_csv(os.path.join(a.out, "clean_digit_level.csv"), index=False)

    # --- descriptives ---
    per = dig.groupby(["session_id", "condition"])["correct"].mean().unstack()
    desc = pd.DataFrame({"mean": per.mean(), "sd": per.std(), "n": per.count()})
    desc["ci95"] = 1.96 * desc["sd"] / np.sqrt(desc["n"])
    labels = {"A": "Indian style, slow", "B": "Indian style, fast", "C": "Western style, slow", "D": "Western style, fast", "E": "Quiet"}
    desc.index = [f"{c} {labels.get(c, '')}" for c in desc.index]
    log("\nProportion of digits recalled in position (mean over participants):\n" + desc.round(3).to_string())
    desc.to_csv(os.path.join(a.out, "condition_means.csv"))

    music = dig[dig["music"] == 1]
    res = {}
    res["H1"] = gee("correct ~ music + pos_c", dig, log, "H1: music vs quiet (all blocks)")
    res["H2"] = gee("correct ~ style_c * tempo_c + pos_c", music, log, "H2: style x tempo (music blocks)")
    res["H3"] = gee("correct ~ style_c * famC_z + tempo_c + pos_c", music, log, "H3: style x Carnatic familiarity (music blocks)")
    if music["device"].nunique() > 1:
        res["H2_device"] = gee("correct ~ style_c * tempo_c + pos_c + C(device)", music, log, "Exploratory: H2 adjusted for device (phone vs computer)")
    clean = music[(music["tab_hidden"].fillna(0) == 0) & (music["resumes"].fillna(0) == 0)]
    res["H2_sens"] = gee("correct ~ style_c * tempo_c + pos_c", clean, log, "Sensitivity: H2 without hidden-tab or resumed blocks")

    blk = music.groupby(["session_id", "block_position", "style_c", "tempo_c"], as_index=False)["correct"].mean()
    blk["pos_c"] = blk["block_position"] - 3
    log("\n--- Robustness: linear mixed model on block proportions (random intercept per participant) ---")
    if blk["session_id"].nunique() >= 3:
        lmm = smf.mixedlm("correct ~ style_c * tempo_c + pos_c", blk, groups=blk["session_id"]).fit()
        log(lmm.summary().tables[1].to_string())

    rat = d[(d["task"] == "rating") & (d["stimulus"] == "indian") & d["session_id"].isin(dig["session_id"].unique())].copy()
    log("\n--- Manipulation check: 'How Indian did the music sound?' (1-5) ---")
    if len(rat):
        rat["response"] = rat["response"].astype(float)
        rat["style_c"] = rat["style"].map({"raga": 0.5, "western": -0.5})
        rat["tempo_c"] = rat["tempo"].map({"fast": 0.5, "slow": -0.5})
        rat["pos_c"] = rat["block_position"] - 3
        log(rat.groupby("style")["response"].agg(["mean", "std", "count"]).round(2).to_string())
        if rat["session_id"].nunique() >= 3:
            mm = smf.mixedlm("response ~ style_c + tempo_c + pos_c", rat, groups=rat["session_id"]).fit()
            log(mm.summary().tables[1].to_string())

    # --- figures ---
    try:
        import matplotlib; matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 2, figsize=(11, 4))
        order = [i for i in desc.index]
        ax[0].bar(range(len(order)), desc["mean"], yerr=desc["ci95"], color=["#2f5d50", "#2f5d50", "#8a6d3b", "#8a6d3b", "#888"][:len(order)], capsize=4)
        ax[0].set_xticks(range(len(order))); ax[0].set_xticklabels([o.split(" ", 1)[1] for o in order], rotation=20, ha="right")
        ax[0].set_ylabel("Proportion correct in position"); ax[0].set_ylim(0, 1); ax[0].set_title("Recall by condition (95% CI)")
        spc = dig.groupby(["condition", "serial_position"])["correct"].mean().unstack(0)
        for c in spc.columns:
            ax[1].plot(spc.index, spc[c], marker="o", label=labels.get(c, c))
        ax[1].set_xlabel("Serial position"); ax[1].set_ylabel("Proportion correct"); ax[1].set_ylim(0, 1)
        ax[1].set_title("Serial position curves"); ax[1].legend(fontsize=8)
        fig.tight_layout(); fig.savefig(os.path.join(a.out, "recall_figures.png"), dpi=150)
        log(f"\nFigure: {os.path.join(a.out, 'recall_figures.png')}")
    except Exception as e:
        log(f"(figures skipped: {e})")

    for k, t in res.items():
        if t is not None:
            t.to_csv(os.path.join(a.out, f"model_{k}.csv"))
    open(os.path.join(a.out, "summary.txt"), "w", encoding="utf8").write("\n".join(lines) + "\n")
    print(f"\nWrote {a.out}/summary.txt and model tables.")


if __name__ == "__main__":
    main()
