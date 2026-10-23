# Analysis

Pre-registered analysis of the serial-recall data. Needs Python with `pandas`, `statsmodels` and `matplotlib`.

1. Download the whole DataPipe Google Drive folder (Drive: right-click the folder, Download) and unzip it.
2. Run:
   ```
   python analyze.py PATH/TO/UNZIPPED_FOLDER --out results
   ```
3. Read `results/summary.txt`. Also written: `condition_means.csv`, `model_*.csv` (one table per model), `recall_figures.png` (condition means and serial-position curves), `clean_digit_level.csv` (the analysed data).

What it does, in order (details at the top of `analyze.py`): picks one file per session (final `_trials.csv`, else the latest `_progress_b<N>` file), applies the exclusions, scores every digit as correct in position or not, then fits:
- H1 music vs quiet, H2 tempo, H3 Indian vs Western style, H4 style × Carnatic familiarity (logistic GEE at the digit level, clustered by participant);
- a sensitivity refit without hidden-tab or resumed blocks, a linear mixed model on block proportions, and the "how Indian" manipulation check.

`simulate.py` writes fake data in the website's exact format, with effects you choose, to test the pipeline:
```
python simulate.py fake_data --n 40 --music -0.30 --style 0.25 --tempo -0.15 --style-fam 0.20
python analyze.py fake_data --out fake_results
```
