# VERIFICATION LOG: independent red-team assessment (round 2)

Date: 2026-11-22. Assessor: independent session with no access to the builder's notes, drafts or reasoning. Inputs: this repository clone, the design brief (all sections, including §8 Exercise B and §9 learning science, which round 1 did not have), and the round-1 `ISSUES.md` and `VERIFICATION_LOG.md`.

**Sign-off status: NOT signed off.** Round 1: 22 of 23 findings closed, RT-012 still open. Round 2: 8 new findings (1 blocker, 2 major, 5 minor), all open. See `ISSUES.md`.

---

## 1. Environment

| Item | Value |
|---|---|
| OS | Linux 6.18 (container) |
| Python | 3.13.18; numpy 2.2.6, pandas 2.3.0, scipy 1.15.3 (match `programs/requirements-lock.txt`); pyreadstat 1.2.9 and statsmodels present (used only to run the shipped project pipeline) |
| R | 4.3.3; survey 4.2.1, haven 2.5.4, jsonlite 1.8.8 (match `programs/R-packages.lock`) |
| Browser | Playwright + headless Chromium, Node v22.23.5 |
| Network | api.crossref.org reachable (used for DOIs). census.gov not used: data were pre-placed. |
| Clone | HEAD `6e10413`, working tree clean before the runs |

## 2. Data and documents

| File | SHA-256 (assessor) | Documented | Result |
|---|---|---|---|
| `data/nschlc_2024_puf.dta` | `d483c989…99799ce` | `data-notes/README.md` | match |
| Annual NSCH zips 2016–2025 (10 enhanced, `data/annual_nsch/`) | all 10 computed | `data-notes/annual_nsch_download_log.csv` | all 10 match |
| NSCH-LC Methodology Report PDF (project evidence folder) | `8dacb119…24c1a8af` | `data-notes/census_excerpts.md` | match |
| NSCH-LC Source and Accuracy Statement PDF | `7872a140…69926ac47` | `data-notes/census_excerpts.md` | match |
| Pipeline code copies | `sha256sum -c SHA256SUMS` | `data-notes/logged_reference/pipeline/SHA256SUMS` | 7/7 OK |

The Census PDFs and the NSCH *Guide to Multi-Year Estimates* (6 Oct 2025) and *Weighting and Imputation Enhancements* (25 Apr 2024) notes were found outside the repo (project evidence folder; `data/annual_nsch/`) and read with `pdftotext -layout`.

## 3. Programs re-run (from the clone root)

| # | Command | Exit | Wall time | Key output | Self-check |
|---|---|---|---|---|---|
| 1 | `python3 programs/core/decomposition_lab_core.py` | 0 | 49 s | n 12,977; gap 9.77 (5.52, 14.03); explained 8.19 (3.64, 12.74); unexplained 1.58 (−2.95, 6.11); bootstrap gap (5.73, 13.82); earlier rule n 13,103, 9.67 / 8.89 / 0.78; no-preventive earlier rule n 13,143, 9.66 / 8.85 | 107 PASS, 0 FAIL |
| 2 | `Rscript programs/core/decomposition_lab_core.R` | 0 | 40 s | same points | 119 PASS, 0 FAIL |
| 3 | `python3 programs/exercise-a/exercise_a_access_gap.py` | 0 | 73 s | preventive A: gap 13.22, LPM 13.18, Fairlie (English) 15.15, pooled 11.51; B (same children, n 13,564): LPM 12.13, Fairlie 13.45; usual source A: gap 21.85, LPM 7.34, Fairlie 7.51, pooled 12.66; traps-in preventive gap −1.68 | 11 PASS, 0 FAIL (+2 INFO) |
| 4 | `Rscript programs/exercise-a/exercise_a_access_gap.R` | 0 | 127 s | R = Python to ≤1e-12 on every point | 57 PASS, 0 FAIL (+4 INFO: Fairlie bootstrap lower limits differ 0.11–0.76 pp, different RNGs) |
| 5 | `python3 programs/exercise-b/exercise_b_care_navigation.py` | 0 | ~2.5 min | 431,222 children, 102 strata; flow 103,751 → 35,392 → 13,400 → 13,301 → 13,174; Oaxaca n 13,044 (12,139 / 905): gap −2.57 (−8.84, 3.70), explained −1.10 (−5.12, 2.91); DFL explained −0.94 (−6.96, 5.08), ESS 156; LOYO gap −4.95 to −0.79; skip trap n 5,989, gap −8.47 | 6 PASS, 0 FAIL |
| 6 | `Rscript programs/exercise-b/exercise_b_care_navigation.R` | 0 | 6 min 3 s | same points; DFL CI (R RNG) (−6.75, 4.87) | cross-check 72 PASS, 0 FAIL |
| 7 | `python3 programs/build_lab_data.py` | 0 | <1 s | `lab/assets/lab-data.js` (95 KB) | n/a |
| 8 | `python3 lab/_src/build_site.py` | 0 | <1 s | 9 pages + `why-this-lab-works.md` | n/a |

**Comparison with committed outputs:** after runs 1–8, `git status` / `git diff --stat` showed **no changes** (only the assessor's `ISSUES.md` untracked). Every committed JSON, run log (Python and R), `lab-data.js` and built page is byte-identical to the re-run, bootstrap intervals included.

Note on runs: the first attempt to start the R chain in parallel failed because of a shell `cd` scoping mistake by the assessor; the R programs were then run sequentially after their Python counterparts (R Exercises A and B read the Python JSON for their cross-checks). A stray copy of the first R chain may have run the R Exercise A program a second time concurrently; both copies write the same files, and the final outputs are byte-identical to the committed ones.

## 4. Independent statistical checks (assessor scripts, outside the repo)

### 4.1 The brief's §5.2 decomposition, intervals included (RT2-001)

Script `ci_probe.py` (lab's `prepare()` + `labsvy`): earlier caregiver rule, Taylor, Rubin-pooled: gap 9.67 (5.49, 13.84), explained 8.89 (4.38, 13.40), same as the repo. Same with Wave-1 `FIPSST` strata: identical partition (explained limits 4.40, 13.38 differ only by df handling). With income = mean of the six implicates (single fit): points 9.67 / **8.91** / **0.76**, demographics **2.43** (the brief's values exactly); Taylor limits still (5.49, 13.84).

Script `boot_probe.py`: same inputs, the original program's bootstrap (n_h PSUs per stratum with replacement, no rescaling, `default_rng(20261117)`, 200 replicates, SD × 1.96, strata in order of first appearance over the 13,607 rows with outcome and language observed, HHID order):

| Term | Brief §5.2 | Assessor |
|---|---|---|
| gap | 9.67 (5.55, 13.78) | 9.67 (5.55, 13.78) |
| explained | 8.91 (4.56, 13.25) | 8.91 (4.56, 13.25) |
| unexplained | 0.76 (−3.55, 5.07) | 0.76 (−3.55, 5.07) |
| global symptoms | 3.37 (1.80, 4.93) | 3.37 (1.80, 4.93) |
| other attention | 2.19 (0.33, 4.05) | 2.19 (0.33, 4.05) |
| demographics | 2.43 (−0.72, 5.58) | 2.43 (−0.72, 5.58) |
| access | 0.64 (−0.30, 1.58) | 0.64 (−0.30, 1.58) |
| concrete covariates | 0.28 (−0.50, 1.07) | 0.28 (−0.50, 1.07) |
| no-preventive sensitivity | n 13,143; 9.66 (5.56, 13.76); 8.86 (4.53, 13.20) | n 13,143; 9.66 (5.56, 13.76); 8.86 (4.53, 13.20) |

Both Wave-1 `FIPSST`+raw `STRATUM` and `FIPSSTO`+recoded `STRATUM` give the same output: Wave-1 `FIPSST` equals `FIPSSTO` for all 21,768 children (Wave 2: 20,840 equal, 928 differ), and Wave-1 STRATUM takes only "1" and "2A".

### 4.2 The shipped original program (RT2-002)

`original/nsch-lc-adhd-language-gap-replication-2026-11-17.py --skip-download --sections E,F` in a scratch folder (stopped after the primary specification):
- Section E (Tier 2, all ages): complete-case n 21,204; gap 10.90 (8.01, 13.79); explained 5.02 (1.71, 8.32); unexplained 5.88.
- Section F `primary_6to17`: complete-case n 11,928 (input 13,607); gap 8.78 (3.87, 13.70); explained 7.00 (1.42, 12.59); unexplained 1.78; blocks 3.27 / 0.04 / 0.34.

### 4.3 The shipped reviewed pipeline (RT-007, RT2-007)

`nsch_lc_adhd_language_gap.py --data <PUF> --out-dir <scratch>`: "Completed and verified" in 28 s. `evalues_risk_ratio.csv`: Spanish RR 0.2333 (0.1063, 0.5121), E-value 8.04 (3.32); other non-English 0.1283 (0.0642, 0.2564), 15.08 (7.26); model n 13,485, 1,292 events. Equal to the logged file to 7e-15. Shared rows of `decompositions_mi_pooled.csv` (175) and `models_mi_pooled.csv` (157) equal the logged values to ≤1e-12 on coef, SE, CI, p, n; the re-run has 41 and 28 extra rows; variance columns differ by a factor of 10,000; `descriptive_statistics.csv` column sets differ.

### 4.4 Exercise B checks

- Population/outcome rules read against the code and the NSCH-LC Variable List rows (K5Q20_R universe "Skip if S4Q01=2"; K5Q21 "Skip if S4Q01=2 or K5Q20_R=3"; K5Q22 "Skip if K5Q21 in (2, .L)"; all three "N" for 2024). Coding is consistent with the brief's need definition (K5Q20_R = 1 or K5Q21 = 1).
- Pooled design vs the *Guide to Multi-Year Estimates* (Oct 2025): weight ÷ number of years, "2A" → "2", `egen stratacross=group(fipsst stratum)`, enhanced ("e") files only: all as the program does. Weight revision dates (2021 in Oct 2023, 2016–2020 in Apr 2024) confirmed in the 25 Apr 2024 note.
- Year-specific strata (1,020) instead of 102: gap and explained intervals change by ≤0.01 pp (`ess_probe.py`), so the choice does not matter here.
- DFL effective sample size: survey weights alone give English ESS 2,674; the reweighting factor alone gives 306; combined 156. The page's reading (thin overlap) is supported.
- Brief §8 figures (26,021; 7.6% vs 26.4%; −18.8 pp; 0.29; 6.44) are not reproduced; the repo says so and why (`data-notes/exercise_b_outcome.md`, `programs/exercise-b/README.md`). Accepted as disclosed; not verified either way.

### 4.5 Other recomputations

Skip counts (1,249 / 37 / 13 / 12 / 49), PSC complete-item scoring (2.398 vs 1.535), out-of-range LPM shares (20.9% / 33.8%), subset-vs-domain SE (1.813 vs 1.818, df 765 vs 21,666) and sensitivity rows were read from `core_results.json` and checked against the page text and quizzes.

## 5. Lab click-through (headless Chromium, `file://`)

Script `pw.js`: all 9 pages at **1280×800 and 375×800**.

| Check | Result |
|---|---|
| Console errors / warnings / page errors | 0 on all 18 loads |
| Network requests other than file:/data:/blob: | 0 |
| Placeholders in body text (`undefined`, `NaN`, `{{`, `n/a`, `[missing`, `[exA.`, `[exB.`) | 0, before and after clicking every quiz option and opening every model answer |
| Empty `data-num` / `data-ci` elements | 0 |
| Horizontal overflow | 0 px on all pages at both widths |
| Quizzes | 25 items, every option clicked (94 clicks per width); no template errors in any feedback |
| Exercise B section | filled: sample flow, descriptives, both decompositions, LOYO, period/weight tables, skip trap, 3 quizzes, writing task; every number matches the run-5 output |
| Quiz answer position (`quizpos.js`, same hash as `app.js`) | 4-option items: correct option 1st/2nd/3rd/4th in 4/6/5/4 items; 3-option items: 1st/2nd/3rd in 1/2/3 items; longest option in 23 of 25 items (RT-012) |
| Writing checklists (`pw_check.js`) | "X, not Y, causes …" passes the causal-language check in Modules 1 and 5 and both exercises; plain "Language causes the gap." is flagged (RT2-003). Exercise B "interval" item passes on "special" (RT2-005). |
| Reproduce checker with 9.67 / 8.91 / 0.76 | "0.104 pp away", earlier-caregiver-rule diagnosis on all three (RT-009 fixed) |
| Sandbox | prediction echoed; Case C "about the same" accepted; hints case-specific (RT-010, RT-011 fixed) |
| Internal links | all resolve; external links are census.gov and doi.org only |

Not repeated in round 2: keyboard-only walk-through, localStorage-blocked run, the exporter (code paths unchanged since round 1 except those listed).

## 6. Prose numbers against outputs

Exercise B page: "gap is small, negative … interval includes zero" (−2.57; −8.84, 3.70), "changes sign between periods" (−5.40 vs 3.99), LOYO range −4.95 to −0.79, ESS 156 of 12,139, largest share 4.7% (max over implicates 0.0465), skip trap 22.29% / 31.87%, gap −8.47: all match. Exercise A note and `exa-1..4`: match run 3. Module 5 earlier-rule row and text (n 13,103; demographics 1.73 → 2.41): match run 1. "In every specification … explained part stays positive and more than half of the gap": true for all six rows (0.72–0.94). README "bootstrap and Taylor agree within 0.5 pp": largest difference 0.35 pp. Source page "30 rows": 30 rows in `reconciliation.md`.

## 7. Census quotations (`data-notes/census_excerpts.md`)

Each quotation was searched (whitespace-normalised) in the `pdftotext` output: telephone-assistance languages (MR PDF p. 11), FWC/raking (MR p. 35), Taylor/strata/PSU sentences, SAS and Stata lines (S&A p. 6): all verbatim, page numbers correct. Response rate 43.0% (MR PDF p. 4, also p. 19). Inaccurate glosses: RT2-004.

## 8. Citations

All 26 DOIs in `references/references.md` and on the pages resolved on api.crossref.org (HTTP 200; Sweller via the encoded path) with matching authors, year, title, journal, volume, issue and pages; Renkl et al. (2002) has four authors (Staley), as now cited. The brief's Cepeda DOI `10.1037/1089-2680.10.4.354` returns 404, as `references.md` says. Claims on `why-this-lab-works.html` checked against the assessor's knowledge of the sources: Locke & Latham (learning vs performance goals for complex tasks, discussed in the review), Cepeda et al. (optimal gap grows with retention interval), Roediger & Karpicke (prose passages, delayed tests), Kornell et al. (trivia and word pairs; extrapolation stated), Chi et al. (correlational), Hattie & Timperley, Bandura, Mayer & Moreno, Pashler et al.: each row's finding and limit is a fair paraphrase. No neuroscience framing remains. The dropped Schultz et al. principle is not listed as a change from the brief (RT2-008).

## 9. What the assessor could NOT verify

- Downloading from the §5.1 and annual NSCH URLs (files were pre-placed; checksums match the logs).
- A clean install from the lockfiles (locked versions were already installed).
- The CAHMI navigation algorithm and the brief's §8 figures.
- The full output of the original program's Section F sensitivities (run stopped after the primary specification), and the source of the brief's all-ages n 18,042 (the program gives 21,204 complete cases for the same 10.90 / 5.02).
- Phone hardware and screen readers (375 px emulation only).

## 10. Statement

Every command above was run by the assessor in this clone or in a scratch copy of shipped code, and every figure is from those runs. The programs run end to end in both languages for the core study and both exercises, and reproduce their committed outputs byte for byte. The lab renders without errors or missing numbers at both widths and makes no network requests. Round 1's substantive findings are fixed. The sign-off is withheld because the repo still says the brief's intervals and two of its specifications cannot be reproduced when the repository's own shipped code reproduces them exactly (RT2-001, RT2-002), and because the writing checklists accept plain causal claims (RT2-003). **Not signed off.**
