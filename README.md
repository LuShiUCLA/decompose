# Decomposition Learning Lab

A free, self-paced lab that teaches the **twofold Oaxaca–Blinder decomposition on survey data** by having you reproduce a real study from the raw U.S. Census public-use file, break it on purpose, and defend it.

**Open the lab:** https://lushiucla.github.io/decompose/ (runs in any web browser; nothing to install, no sign-in, no tracking).

**The study.** In the NSCH Longitudinal Cohort (2018/2019 baseline, 2024 follow-up), caregivers in English-language households reported an ADHD diagnosis for 16.29% of children aged 6–17, versus 5.97% in other-language households. On the 12,977 children with complete data the gap is 9.77 percentage points; differences in measured characteristics account for 8.19 pp of it. "Accounted for" means **composition, never cause**.

**Your goal.** Reproduce the headline (gap, explained, unexplained) within ±0.1 pp, then defend each modelling choice.

## Start in five minutes

1. **Open the lab.** Open `lab/index.html` in a browser (or the GitHub Pages site once published). No login, no server, no tracking. Progress is stored only in your browser.
2. **Install** Python 3.12+ (`pip install -r programs/requirements-lock.txt`) and/or R 4.3+ (packages in `programs/R-packages.lock`).
3. **Run the core program** from the repository root:
   ```
   python programs/core/decomposition_lab_core.py
   Rscript programs/core/decomposition_lab_core.R
   ```
   The first run downloads the Census Stata file (about 5.5 MB zipped) into `data/`. Each program runs a synthetic dry run, the decomposition, a PSU bootstrap, sensitivity and falsification checks, and ends with a PASS/FAIL self-check. Python takes well under a minute.
4. **Type your three numbers** into the checkpoint on the lab's start page.

Details: `programs/README.md`.

## What is in the repository

| Path | What it is |
|---|---|
| `lab/` | The static web lab (GitHub Pages source). Pages are assembled by `lab/_src/build_site.py` from `lab/_src/pages/`. |
| `programs/core/` | The study's decomposition, Python and R, with logged outputs in `output/`. |
| `programs/exercise-a/` | Exercise A: the language gap in access to care (LPM and Fairlie decompositions, traps in and out). |
| `programs/exercise-b/` | Exercise B: care navigation in the pooled annual NSCH 2016–2025. See its README for status. |
| `programs/lib/` | Shared survey and decomposition code (`labsvy`) and the file preparation (`nschlc_prepare`), one Python and one R version of each. |
| `programs/build_lab_data.py` | Copies program output into `lab/assets/lab-data.js`. |
| `data-notes/` | Provenance, checksums, codebook rows relied on, the reference values and the reconciliation of the design brief. |
| `references/` | Every reference with its DOI, and how each was checked. |
| `ISSUES.md`, `VERIFICATION_LOG.md` | The independent red-team review and its record. |

## Where the numbers come from

Every number on every page is read from program output; none is typed into the HTML.

```
public-use file → programs/core/*.py, *.R → output/*.json → programs/build_lab_data.py → lab/assets/lab-data.js → pages
```

The **reference values** the self-checks compare against are the logged outputs of the project's earlier, reviewed analysis pipeline (see "Work that predates this lab" below). Copies of those output tables are in `data-notes/logged_reference/`, and `data-notes/make_reference_values.py` converts them into `data-notes/reference_values.json`. The R program also checks its hand-coded standard errors against the `survey` package.

The design brief for this lab quoted a decomposition with n = 13,103, gap 9.67 (5.55, 13.78) and explained 8.91 (4.56, 13.25). Every one of those figures, intervals included, reproduces exactly with the method of the project's superseded first program (copied in `data-notes/logged_reference/pipeline/original/`): (1) an earlier caregiver mental-health rule that codes 'not poor' when caregiver 1 answered even if a present second caregiver did not; (2) income as the mean of the six imputed values in one fit, which ignores imputation uncertainty; and (3) a bootstrap that draws n_h households per stratum without the Rao–Wu rescaling. Both core programs run this method (`brief_method()`) and check it against the brief. The lab's headline uses the reviewed pipeline and the AJPM manuscript's choices instead: every present caregiver must have answered, Rubin's rules over the six implicates, and Taylor intervals (n = 12,977, gap 9.77, explained 8.19). The brief's PSC means reproduce when the five items are summed over children with all five answered (the released `PSCATT` scores an unanswered item as 0). Its 'earlier specification' (n 11,928; gap 8.78; explained 7.00) reproduces from the superseded program; its all-ages figures (gap 10.90, explained 5.02) reproduce there too, on 21,204 children; the brief's n of 18,042 belongs to a different specification in the same run (an all-ages sensitivity with gap 9.64). Neither is used. `data-notes/reconciliation.md` lists every brief figure, the reproduced value and the status.

To rebuild the lab after re-running the programs:
```
python programs/build_lab_data.py
python lab/_src/build_site.py
```

## Work that predates this lab

The lab reuses data and analysis that already existed in the project before this lab was built, rather than downloading and re-analysing them again:

- **Data and documentation** were downloaded from census.gov on 17 November 2026 for the project's research brief and abstract. They are in the project's shared folder `Society of Behavioral Medicine/data/` (public-use file `.dta`, `.zip`, `.do`, Variable List) and `Society of Behavioral Medicine/evidence/` (Methodology Report, Source and Accuracy Statement, imputed-data guide, FAQs). The `.dta` used here has SHA-256 `d483c989…99799ce`, identical to the file in that folder; the programs will download a fresh copy from Census if `data/` is empty.
- **The reviewed analysis pipeline** (`nsch_lc_adhd_language_gap.py`, `survey_engine.py`, `primary_bootstrap.py`, `supplement.py`, `publication.py`) and its logged results (`results/`, run 17 November 2026) are in the same folder; copies of the code as it stood on 22 November 2026 are in `data-notes/logged_reference/pipeline/`. That version is later than the one that wrote the logged tables of 17 November: re-run on 22 November 2026, it writes more rows (216 vs 175 decomposition rows, 185 vs 157 model rows), stores two variance columns on a different scale and changes the descriptive table's columns, but every coefficient, standard error, interval and n the two runs share is identical, as are the risk ratios and E-values. It was written for the study itself; this lab's programs are a new, independent implementation written for teaching, and they reproduce that pipeline's numbers (see the self-check blocks).
- **Annual NSCH files for Exercise B** (2016–2025 Stata files, Topical Variable Lists, the Guide to Multi-Year Estimates and the weighting-revision note) were downloaded to the project owner's computer on 22 November 2026; see `programs/exercise-b/README.md`.

The data files themselves are not committed (`.gitignore`); the Census terms let anyone download them.

## Changes from the design brief, and why

- **Headline specification**: the brief's decomposition used the project's earlier caregiver mental-health rule; the lab uses the reviewed rule (see above) and shows the earlier rule as a sensitivity row in Module 5. The brief's PSC means used complete-item scoring; the lab's descriptives use Census's released `PSCATT` and the reconciliation shows both. The two decomposition specifications that do not reproduce at all are not used. Labels corrected: 16.3% vs 6.0% are 2024 (follow-up) rates, not baseline; the adjusted risk ratio 0.23 is Spanish vs English, and 0.13 is other non-English vs English in the same model.
- **R packages**: `survey` (Lumley, 2004) is used to cross-check standard errors; the decomposition itself is coded directly in both languages so learners can read every step. `srvyr` and the `oaxaca` package are not used: `srvyr` adds no estimator the lab needs, and coding the decomposition by hand is the point of Module 2. Python uses numpy, pandas and scipy; `statsmodels` and `pyreadstat` are not needed (pandas reads Stata files).
- **Survey design variables**: strata are `FIPSSTO` × `STRATUM` (stratum 2A recoded to 2), as the Source and Accuracy Statement specifies; the brief named `FIPSST`. Wave 1 `FIPSST` equals `FIPSSTO` for every child, so the strata are the same; the 2024 `FIPSST` would differ for 928 children (`data-notes/census_excerpts.md`).
- **Decomposition intervals**: the brief asked for PSU-bootstrap standard errors. The lab reports Taylor intervals as primary, because they are deterministic and match the reviewed pipeline's logged run, and shows the PSU bootstrap (Rao–Wu, 200 replicates, seed 20261117) beside them in Module 3. The two agree within 0.5 pp at every limit (self-check).
- **Lonely-PSU options and the logit view**: the brief asked the calculator to show both singleton-stratum conventions and the learner to run the logit version. Module 3's sandbox shows the 'remove' and 'adjust' standard errors side by side as program output, and Interaction 3 shows a precomputed logit result: fitting survey models in the browser would add code the learner cannot check against the programs. Learners run both in the programs.
- **Calculator target**: the live calculator reproduces the reproduced headline (9.77 / 8.19), not the brief's 9.67 / 8.91.
- **Logit vs LPM** uses a reduced covariate set because a logit with every covariate is unstable with only 48 diagnoses among 779 other-language children (from `core_results.json`); the page says so.
- **Prediction-error principle**: the brief listed a 'prediction error' principle citing Schultz, Dayan & Montague (1997), which relates dopamine-neuron activity during reward learning to a temporal-difference model. It does not study instruction, so it cannot support a teaching design, and citing it invites the 'dopamine hit' reading the brief rules out. The lab keeps the predict-before-you-see prompts and grounds them in behavioural evidence (Kornell, Hays & Bjork, 2009) instead.
- **Two-day plan** is kept; the time estimates are the builder's, not measured, and the lab says so where it shows them.

## Builder's additions (flagged in the lab as "builder's addition")

1. **Predict the split before you learn it** (Module 1). You drag six sliders to guess how the gap splits, then see the actual split. It rests on the evidence that attempting an answer before seeing it improves later learning when feedback follows (Kornell, Hays & Bjork, 2009). You gain a concrete record of your own prior, which makes the attention-items result memorable.
2. **Mock seminar** (Module 5). Three adversarial questions a discussant would ask (circularity of symptom covariates, choice of reference, out-of-range LPM predictions), each with defences scored and explained using the study's own numbers. It mirrors how methods are actually defended in seminars and peer review, and it practises retrieval in a new form.
3. **Manuscript table export** (Module 5). Load your own `core_results.json` (read locally in the browser) and download a Markdown table with a methods footnote. You gain a reproducible bridge from your run to a manuscript, and a second check that your numbers match.

## The four "deeper version" questions

1. *What would a top professional do that the brief does not ask?* Reconcile every quoted number against logged runs before teaching it, implement the variance estimator twice (by hand and with `survey`), and disclose LPM out-of-range predictions rather than hide them.
2. *What is the rawest material?* The Census Stata file, the Variable List rows (Universe and skip columns) and the Source and Accuracy Statement, not summary tables. The codebook rows the lab shows are copied from the Variable List.
3. *Which methods and tools?* Influence-function (Taylor) variances with PSUs within strata, domain estimation, Rao–Wu rescaled PSU bootstrap, Rubin's rules over the six income implicates, Fairlie decomposition over all block orderings, DFL reweighting for Exercise B.
4. *What, other than the builder, shows it is right?* The logged outputs of the earlier pipeline, agreement between the independent Python and R implementations, the `survey` package, synthetic data with known answers, falsification checks that must move, and an independent red-team review (`ISSUES.md`, `VERIFICATION_LOG.md`).

## Licence

Content (text, pages, quizzes) CC BY 4.0; code MIT. See `LICENSE`. The NSCH-LC and NSCH data are U.S. Census Bureau products; this lab is not affiliated with or endorsed by the Census Bureau.
