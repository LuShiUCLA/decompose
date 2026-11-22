# Running the programs

All commands run from the repository root. Each program has **one line to edit** if your data live elsewhere: `DATA_PATH` near the top. If the file is missing, the core and Exercise A programs download the official Census zip into `data/` and extract `nschlc_2024_puf.dta`.

## Install

| Language | Version used for the logged runs | Install |
|---|---|---|
| Python | 3.13.18 (3.12 also works with the same packages) | `pip install -r programs/requirements-lock.txt` |
| R | 4.3.3 | `survey` 4.2.1, `haven` 2.5.4, `jsonlite` 1.8.8 (see `R-packages.lock`) |

## Programs

| Program | What it does | Output |
|---|---|---|
| `core/decomposition_lab_core.py` / `.R` | Synthetic dry run; descriptives (domain estimation); primary decomposition (LPM, English reference, Taylor variance, Rubin over six income implicates); Rao–Wu PSU bootstrap (200 replicates, seed 20261117); reference-coefficient variants; logit vs LPM; sensitivity specifications; falsification checks; PASS/FAIL self-check against `data-notes/reference_values.json` | `core/output/core_results*.json`, `core_run_log*.txt` |
| `exercise-a/exercise_a_access_gap.py` / `.R` | Preventive visit and usual source of care: LPM Oaxaca–Blinder and Fairlie (all 120 block orderings, PSU bootstrap of the aggregate), with and without the circular "other access" block, and with both traps in. The R program cross-checks every figure against the Python output. | `exercise-a/output/` |
| `exercise-b/` | See `exercise-b/README.md`. | |
| `build_lab_data.py` | Copies the JSON outputs into `lab/assets/lab-data.js` for the web lab. | |

Run time on the reference machine: about 40 seconds for the Python core program and 35 seconds for the R core program. Exercise A takes about 1 minute in Python and 2 minutes in R (the Fairlie bootstrap refits a logit 200 times per implicate and specification). Exercise B takes about 2.5 minutes in Python and 6 minutes in R.

## What PASS/FAIL means

Tolerances are written next to each check in the code: ±0.05 pp for point estimates and confidence limits against the logged reference run (±0.005 for the attention-score mean, which is on a 0–10 scale), exact (1e-9) for the decomposition identities, and ±0.5 pp for bootstrap limits against Taylor limits (Monte Carlo error with 200 replicates). The bootstrap limits from R differ from Python's because the two languages use different random-number generators; point estimates are identical.

## Falsification checks: what should move

| Check | Expected result | If it does not move |
|---|---|---|
| K4Q20R skips dropped instead of coded 0 | other-language preventive rate rises from about 73% to about 99% | your code is not reading S4Q01 |
| CURRCOV instead of CURRINS | insured rates rise by less than half a point (English 96.91% to 97.36%); 65 children aged 6–17 (93 in the cohort) change status | your code is not reading the variable you think |
| Pre-subset instead of domain | 14 singleton strata appear, design df falls from 21,666 to 765 | you are not declaring the design on the full file |
| Model n vs design-matrix n | 12,977 vs 13,021 (44 children lack the outcome) | your n is not the model's n |

The exact numbers are printed by the programs; the values above are from the logged run.
