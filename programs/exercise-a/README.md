# Exercise A: the language gap in access to care

**Question.** Among children aged 6–17 in the NSCH-LC 2024 follow-up, how much of the household-language gap in two access-to-care outcomes is compositional?

- `PREVENTIVE_W2`: at least one preventive visit in the past 12 months (K4Q20R, with S4Q01 = 2 coded as zero visits: Trap 1).
- `USUAL_SOURCE_W2`: a usual place for sick care (K4Q01).

The covariate blocks and the reasons for each are in `data-notes/exercise_a_covariates.md`. Because the outcome and blocks differ from the core study, so does the complete-case sample (n = 13,564 for preventive visits, against 12,977 in the core study).

## Run

```
python programs/exercise-a/exercise_a_access_gap.py
Rscript programs/exercise-a/exercise_a_access_gap.R   # run after Python: it cross-checks every figure
```

Both programs also run when pasted into a console (they find or download the lab folder; see `programs/README.md`). The one line to edit is `DATA_PATH`. If the file is missing, the programs download the Census zip into `data/`. Run time on the reference machine: about 1 minute in Python and 2 minutes in R.

## What the programs do

1. **Synthetic dry run** with a known answer.
2. **LPM Oaxaca–Blinder** with English coefficients, Taylor intervals, Rubin's rules over the six income implicates.
3. **Fairlie (2005) logit decomposition** with English logit coefficients, detailed contributions averaged over all 120 block orderings, and a PSU bootstrap (200 replicates) of the aggregate. A pooled-logit version is reported alongside.
4. **Three specifications per outcome**: A, all blocks; B, without the other access outcome (circularity check, same children as A); C, both traps in (skips dropped, CURRCOV) as a falsification run.
5. **Self-check**: identities, same children in A and B, descriptives against the logged reference (±0.05 pp), and the traps must move the preventive-visit gap. R cross-checks every figure against the Python output.

## Output

`output/exercise_a_results.json` (read by the web lab), `output/exercise_a_run_log.txt`, and the R equivalents (`*_R.*`).
