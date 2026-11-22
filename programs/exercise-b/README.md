# Exercise B: care navigation, pooled annual NSCH 2016–2025

**Question.** Among publicly insured children with special health care needs (CSHCN) who needed help coordinating their care, how much of the household-language gap in effective care navigation (versus unmet need) is compositional?

**Why the annual NSCH, not the NSCH-LC file.** The coordination items K5Q20_R, K5Q21 and K5Q22 are marked **N** for 2024 in the NSCH-LC Variable List (`data-notes/codebook_excerpts.md`): they were not asked at the 2024 follow-up.

## Run

```
python programs/exercise-b/harmonise_codebook.py        # optional: rebuilds the harmonisation log
python programs/exercise-b/exercise_b_care_navigation.py
Rscript programs/exercise-b/exercise_b_care_navigation.R  # run after Python: it cross-checks every figure
```

The one line to edit is `ANNUAL_DIR`. If the files are missing, the programs download the ten enhanced Stata files (`nsch_<year>_topical_Stata.zip`, 2023 is `nsch_2023e_topical_Stata.zip`) and the three original 2016–2018 files from `https://www2.census.gov/programs-surveys/nsch/datasets/<year>/` (about 52 MB of zip files, plus 46 MB for the three original files). R writes `output/exercise_b_run_log_R.txt`. Download log with SHA-256: `data-notes/annual_nsch_download_log.csv`.

Run time on the reference machine: about 2.5 minutes in Python and 6 minutes in R (the DFL bootstrap refits a logit 1,200 times).

## What the programs do

1. **Harmonise** ten files. Every variable's labels, year by year, are in `data-notes/exercise_b_harmonisation.md` (generated from the Census `.do` files). Decisions: stratum "2A" recoded to "2" (2016 had strata 1 and 2); race codes 3, 5, 6, 7 collapsed into "other or multiple" (code 6 is labelled for 2016–2018 but absent from the enhanced files); `INSTYPE` 1 and 3 define public coverage in every year (code 4, "type unspecified", exists only in 2016 and is excluded); income `FPL_I1`–`FPL_I6` is top- and bottom-coded at 400 and 50 in every year.
2. **Population and outcome**: `data-notes/exercise_b_outcome.md`. The K5Q22 skip (asked only if extra help was needed) is information, not missingness.
3. **Oaxaca–Blinder** on the LPM with English coefficients, survey year as its own block (year fixed effects), Taylor variance on the pooled design, Rubin's rules over six income implicates.
4. **DFL reweighting** (DiNardo, Fortin & Lemieux, 1996) as a second decomposition family, with a PSU bootstrap and a reweighting diagnostic (effective sample size).
5. **Falsification**: leave one year out; 2016–2021 (re-released files) vs 2022–2025; original vs enhanced weights for 2016–2018; the K5Q22 skip trap.
6. **Self-check** (identities, DFL gap = Oaxaca gap, no singleton strata, the trap moves n) and, in R, a figure-by-figure cross-check against the Python output.

## Design-brief items that changed

- **"Medicaid-enrolled"** became "publicly insured" (`INSTYPE` 1 or 3): the public-use file does not separate Medicaid from other government plans.
- **The "CAHMI algorithm"** for navigation was not available to the builder; the outcome is defined from the questionnaire routing and documented. The brief's figures for that analysis (26,021; 7.6% vs 26.4%; −18.8 pp; 0.29; 6.44) are not reproduced or used.
- **Pre- vs post-revision weights** is run for 2016–2018 only, the years for which Census still posts the original files.

Results are shown on the lab's Exercises page and in `output/exercise_b_run_log.txt`.
