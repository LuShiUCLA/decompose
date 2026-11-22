# ISSUES: independent red-team review, round 2

Assessor: independent red-team session (no access to the builder's notes). Review date: 2026-11-22.
Clone reviewed: HEAD `6e10413` ("Fix red-team round 1: brief reproduces under earlier caregiver rule; like-for-like Fairlie; Exercise B page").
Inputs: this repository and its outputs, the design brief (§5 reference values and rules, §8 Exercise B, §9 learning science, §10–§13 checklist and definition of done), and the round-1 `ISSUES.md` / `VERIFICATION_LOG.md`.
How each finding was checked is in `VERIFICATION_LOG.md`. Severity scale (as in round 1): **blocker** (a §11 box cannot be ticked), **major** (wrong or misleading statistics or teaching, or a required deliverable missing), **minor** (local inaccuracy, unverifiable claim or pedagogy defect).

**Summary.** Round 1: 22 of 23 closed, 1 still open (RT-012). The fix for RT-013 introduced a new defect (RT2-003). New in round 2: 1 blocker, 2 major, 5 minor. All new findings are open.

Assessor scripts referred to below are in the assessor's scratch area, not in the repo; each is short enough to be re-created from the steps given.

---

## Round-1 findings: status

| ID | Status | Evidence (one line) |
|---|---|---|
| RT-001 | closed | Both core programs run the earlier caregiver-MH rule and self-check it against the brief: n 13,103, gap 9.67, explained 8.89, unexplained 0.78, blocks 2.41/3.37/2.19/0.28/0.64; no-preventive n 13,143, 9.66/8.85 (all within ±0.05; 119 PASS in R, 107 PASS in Python). The headline keeps the reviewed rule with a stated reason (Module 5, README). The interval part is re-filed as RT2-001. |
| RT-002 | closed | Core program computes complete-item PSC scoring: 2.398 vs 1.535; ≥7 8.56 (7.43, 9.85) vs 3.61 (1.45, 8.73); reconciliation marks "reproduces (complete-item scoring)"; Module 5 says which score is used. |
| RT-003 | closed | `skip_counts_primary`: 1,249 / 37 / 13 S4Q01-missing, 12 without K4Q20R, 49 total; quiz `m4-a` now says 49 = 37 + 12 (+1 answered child used); prepare.py comment matches code. |
| RT-004 | closed | README "Changes from the design brief" now lists Taylor-as-primary with the reason; Module 3 shows the Rao–Wu bootstrap beside it. (The brief's own intervals: RT2-001.) |
| RT-005 | closed | Exercise A Fairlie now uses English logit coefficients (`coef="A"`); pooled-logit shown as a separate column labelled "different reference"; note and `exa-1` rewritten; matching method described as weighted-quantile, not attributed to Fairlie. |
| RT-006 | closed | Exercise B programs (Python + R) exist and ran end to end in this review (Python 6 PASS; R cross-check 0 FAIL); the page section is filled. Remaining Exercise B defects: RT2-005, RT2-006. |
| RT-007 | closed | Pipeline code is now shipped (`data-notes/logged_reference/pipeline/`, SHA256SUMS OK). Assessor ran `nsch_lc_adhd_language_gap.py` on the PUF: Spanish RR 0.233 (0.106, 0.512), other non-English 0.128 (0.064, 0.256), n 13,485; E-values 8.04 (3.32) / 15.08 (7.26). Labels confirmed. (Provenance wording: RT2-007.) |
| RT-008 | closed | `codebook_excerpts.md` now has HIGRADE, K7Q84_R, MEMORYCOND, A1/A2_MENTHEALTH, A2_RELATION rows. |
| RT-009 | closed | Entering 9.67 / 8.91 / 0.76 now gives "0.104 pp away" and the earlier-caregiver-rule diagnosis; the PSC-rescaling hint is gone. |
| RT-010 | closed | Case C "No meaningful effect (about the same)" is now accepted with an explanation. |
| RT-011 | closed | Step-1 prediction is echoed in the feedback; hints are case-specific. |
| RT-012 | **still open** | Correct-answer positions are now spread (1st–4th), but the correct option is still the longest option in 23 of 25 items. |
| RT-013 | closed | The disclaimer "does not mean that attention causes the gap" is no longer flagged. The fix introduced a worse defect: RT2-002. |
| RT-014 | closed | `seminar-3` now states 21% (English) and 34% (other-language) of fitted values outside [0, 1]. |
| RT-015 | closed | Spec B is fitted on the same children as A (self-check PASS; n 13,564 both; gap 13.22 both). |
| RT-016 | closed | Schultz et al. removed; Cepeda limit reworded (supported); Renkl et al. now lists Staley (Crossref confirms 4 authors); Kornell extrapolation stated; "biggest surprise" claim removed. All 26 DOIs resolve on Crossref with matching metadata. |
| RT-017 | closed | Index page: "The hours are the builder's estimates; no learner has been timed." |
| RT-018 | closed | `data-notes/census_excerpts.md` quotes verified against the Census PDFs (checksums match); see RT2-004 for two inaccurate glosses around them. |
| RT-019 | closed | "not ignorable" removed; programs README now says "less than half a point (96.91% to 97.36%)". |
| RT-020 | closed | Exercise A: descriptive rates checked against logged values, dry run tests both `coef="A"` and pooled, stale comment removed, R run log written and reproduced byte-identically. |
| RT-021 | closed | Accepted with a stated reason in README ("Lonely-PSU options and the logit view"); Module 3 shows remove/adjust SEs as program output. |
| RT-022 | closed | Module 3 text, quiz `m3-b` and `labsvy.py` docstring now say households and children coincide in this file and stratification is what matters. |
| RT-023 | closed | Source page now summarises the reconciliation by category. The remaining inaccuracies in it are RT2-001 and RT2-002. |

---

## RT2-001 — The brief's decomposition intervals reproduce exactly; the repo says their method "is not identified"

- **Severity:** blocker (§11 box 1 requires every §5.2 figure within ±0.05 pp, or a documented, justified methods difference; the documented justification is false)
- **Location:** `README.md` ("Where the numbers come from": "The brief's intervals match neither Taylor nor bootstrap intervals, so their method is not identified"); `lab/source.html` / `lab/_src/pages/08-source.html` (same sentence); `data-notes/reconciliation.md` rows Gap, Explained, Unexplained, global-symptoms block, demographics block, Sensitivity ("interval does not"; "its interval method is not identified"); `data-notes/make_reconciliation.py`.
- **Steps to reproduce:** the method is in the repository's own shipped program, `data-notes/logged_reference/pipeline/original/nsch-lc-adhd-language-gap-replication-2026-11-17.py` (function `oaxaca_blinder`, lines 1114–1200, and `FPL_MEAN_W1`, line 888). Using the lab's `nschlc_prepare.prepare()`:
  1. `CAREGIVER_POOR_MH = CAREGIVER_POOR_MH_EARLIER_RULE`.
  2. Income = mean of the six implicates (`FPL_MEAN_W1`), one fit, no Rubin pooling.
  3. Sample = ages 6–17 with language and `ADHD_EVER_W2` observed (13,607 rows, rows in HHID order); complete cases are dropped inside each replicate.
  4. Bootstrap: `rng = np.random.default_rng(20261117)`; for each of 200 replicates, for each stratum (Wave-1 `FIPSST` + "_" + `STRATUM`, in order of first appearance) draw n_h PSUs with replacement (`rng.choice`, no Rao–Wu rescaling); SE = SD of the 200 replicate estimates (ddof 1); CI = estimate ± 1.96 SE.
- **Expected (brief §5.2):** gap 9.67 (5.55, 13.78); explained 8.91 (4.56, 13.25); unexplained 0.76 (−3.55, 5.07); blocks 3.37 (1.80, 4.93), 2.19 (0.33, 4.05), 2.43 (−0.72, 5.58), 0.64 (−0.30, 1.58), 0.28 (−0.50, 1.07); sensitivity n 13,143, gap 9.66 (5.56, 13.76), explained 8.86 (4.53, 13.20).
- **Actual (assessor run, `ci_probe.py` / `boot_probe.py`):** every one of these figures, point and both limits, to two decimals: 9.67 (5.55, 13.78); 8.91 (4.56, 13.25); 0.76 (−3.55, 5.07); 3.37 (1.80, 4.93); 2.19 (0.33, 4.05); 2.43 (−0.72, 5.58); 0.64 (−0.30, 1.58); 0.28 (−0.50, 1.07); sensitivity n 13,143, 9.66 (5.56, 13.76), 8.86 (4.53, 13.20). Step 2 also explains why the lab's earlier-rule run gives 8.89 / 0.78 / 2.41 rather than 8.91 / 0.76 / 2.43: the brief averaged the implicates before fitting, the lab Rubin-pools (within tolerance, but the repo does not say so).
- **What is needed:** correct the README, Source page and reconciliation (the method is identified: a non-rescaled PSU-within-stratum bootstrap on implicate-mean income), and either reproduce the intervals in both core programs or document the switch to Taylor / Rao–Wu with Rubin pooling as the justified methods difference it is.
- **Status:** open

## RT2-002 — The brief's "earlier specification" and "all-ages Tier 2" figures come out of the shipped original program; the repo says they "do not reproduce at all"

- **Severity:** major (reconciliation verdict wrong for two §5.2 rows; the Source page and README repeat it)
- **Location:** `data-notes/reconciliation.md` rows "Earlier specification, ages 6-17" and "All-ages Tier 2 Oaxaca" ("not in any logged output … **does not reproduce**"); `README.md` ("Two brief figures … do not reproduce at all and are not used"); `lab/source.html` ("appear in no logged output and are not used").
- **Steps to reproduce:** copy `data-notes/logged_reference/pipeline/original/nsch-lc-adhd-language-gap-replication-2026-11-17.py` to an empty folder with the PUF and Variable List in `data/`, then `MPLBACKEND=Agg python3 nsch-lc-adhd-language-gap-replication-2026-11-17.py --data-dir data --skip-download --sections E,F --out-dir out`.
- **Expected (brief §5.2):** earlier specification n 11,928, gap 8.78, explained 7.00; all-ages Tier 2 n 18,042, gap 10.90, explained 5.02.
- **Actual (assessor run):** Section E: gap **10.90**, explained **5.02**, unexplained 5.88 (complete-case n 21,204, not 18,042). Section F `primary_6to17`: complete-case n **11,928**, gap **8.78** (3.87, 13.70), explained **7.00** (1.42, 12.59), unexplained 1.78, global symptoms 3.27, concrete 0.04, access 0.34 (exactly the program header's expected values). The repo ships this program and cites its header for the expected values, but did not run it.
- **What is needed:** mark these rows as reproducing from the superseded program (and say what differs: CURRCOV, the buggy-then-corrected checkup, Wave-1 access, n 21,204 vs 18,042), or explain why they are still rejected.
- **Status:** open

## RT2-003 — The negation guard lets plain causal claims through every writing checklist

- **Severity:** major (§13: the lab must correct the learner every time they use causal language; the Module 5 Results-note checklist now certifies a causal, over-claiming note)
- **Location:** `lab/assets/app.js` lines 124–131 (`checklist`: a flagged phrase is ignored if any of not/no/never/… occurs earlier in the same sentence within 60 characters).
- **Steps to reproduce (headless Chromium, `pw_check.js`):** type each text, press "Get checklist feedback".
  1. Module 1: "If the other-language group had the same distribution of symptoms and characteristics as the English group, how much of the reported diagnosis gap would remain? Access, not symptoms, causes the gap."
  2. Module 5: a 60-word note containing "Attention symptoms, not language, cause the gap, which proves there is no under-diagnosis among other-language children".
  3. Exercise A: "… Insurance, not symptoms, causes the gap in preventive visits …"; Exercise B: "… Language barriers, not composition, caused the remaining difference …".
- **Expected:** "✖ Avoids causal language" in every case (the control sentence "Language causes the gap." is flagged correctly).
- **Actual:** "✔ Avoids causal language" / "✔ Avoids causal and over-claiming verbs" in all four. In case 2 every one of the eight Results-note items is ticked, including the causal-verb and "proves"/"no under-diagnosis" checks. Contrastive "X, not Y, causes …" is the commonest way a learner states a causal conclusion.
- **Status:** open

## RT2-004 — Inaccurate glosses around the strata quotation

- **Severity:** minor
- **Location:** `README.md` "Survey design variables"; `data-notes/census_excerpts.md` ("The design brief wrote `FIPSST` (current state)" and "The same statements appear in the Methodology Report (PDF p. 38)"); `data-notes/reconciliation.md` last row ("variable name corrected").
- **Actual:** (a) The brief's STRATACROSS came from the original program, which builds it from the **Wave-1** row's `FIPSST` (line 840 / 886). In the PUF, Wave-1 `FIPSST` equals `FIPSSTO` for all 21,768 children (Wave 2: 20,840 equal, 928 differ). So the brief's strata are identical to Census's; the "928 children" contrast applies only to Wave-2 `FIPSST`, which neither the brief nor its source program used. The brief never says "current state". (b) Methodology Report PDF p. 38 says to cross `FIPSSTO` with `STRATUM` into 102 levels (`EGEN STRATACROSS = GROUP (fipssto stratum)`), but it does not contain the S&A Statement's Taylor sentence, the SAS lines or the "2A" recode; "the same statements" overstates it. The S&A quotations themselves are verbatim (verified).
- **Expected:** the gloss says the brief's (Wave-1) `FIPSST` and `FIPSSTO` define the same strata, and cites MR p. 38 for what it actually says.
- **Status:** open

## RT2-005 — Exercise B writing checklist: "Reports the gap with its interval" is satisfied by almost any text

- **Severity:** minor
- **Location:** `lab/assets/quizzes.js` `WRITING.exb` items 1–3.
- **Steps:** on `exercises.html`, Exercise B "Write it up", enter a 60-word text that gives no gap and no interval but mentions "special health care needs".
- **Expected:** "✖ Reports the gap with its interval".
- **Actual:** "✔". The keyword `"ci"` matches as a substring of "special", "precise", "decision", "coefficient", "social", so any answer that names the population passes. Item 3's keywords "year" and "weight" (e.g. "past year", "weighted") and item 2's "small" pass similarly without the content asked for.
- **Status:** open

## RT2-006 — Exercise B R program: no run log, and "re-computes every figure" is overstated

- **Severity:** minor
- **Location:** `programs/exercise-b/output/` (no `exercise_b_run_log_R.txt`; core and Exercise A have one); `lab/_src/pages/06-exercises.html` ("the R program re-computes every figure and cross-checks it against the Python output").
- **Actual:** the R program prints to the console only and writes `exercise_b_results_R.json`. It does not recompute the sample-flow counts shown in "Who is analysed", the DFL effective sample size or the largest-weight share, and it compares the DFL interval only as INFO. Its only self-checks are the synthetic dry run and the comparison with the Python JSON (it has no identities or skip-trap check of its own). Same kind of gap as round-1 RT-020 for Exercise A, which was fixed there.
- **Status:** open

## RT2-007 — The shipped "verbatim" pipeline is not the version that wrote the logged reference CSVs

- **Severity:** minor
- **Location:** `README.md` ("verbatim copies of the code are in `data-notes/logged_reference/pipeline/` … The pipeline was re-run on 22 November 2026 and gave identical results"); `data-notes/logged_reference/pipeline/README.md` ("writes the CSVs in `../`").
- **Steps:** run `nsch_lc_adhd_language_gap.py --data <PUF> --out-dir out` (28 s) and compare `out/*.csv` with `data-notes/logged_reference/*.csv`.
- **Actual:** every shared estimate, SE, CI, n and RR agrees to 1e-12, but the files are not identical: `decompositions_mi_pooled.csv` has 216 rows vs 175 logged (two extra specifications), `models_mi_pooled.csv` 185 vs 157 (three extra models), `descriptive_statistics.csv` has a different column set (18 vs 23 columns), and the `within_variance` / `between_variance` columns differ by a factor of 10,000 (pp² vs proportion²). The logged CSVs therefore came from a different revision of the code than the one shipped.
- **Expected:** ship the exact revision that produced the logged files, or say that the shipped copy is a later revision that reproduces every shared estimate.
- **Status:** open

## RT2-008 — Silent departure from brief §9: the prediction-error principle and its citation were dropped without a note

- **Severity:** minor
- **Location:** `README.md` "Changes from the design brief"; `lab/why-this-lab-works.html`.
- **Actual:** brief §9 lists "Prediction error as a learning signal (Schultz, Dayan & Montague, 1997)" as a principle to implement and cite. After round 1 the lab replaced it with Kornell, Hays & Bjork (2009) and Bjork & Bjork (2020), which is a defensible choice (the Why page now says "No neuroscience claims"), but the change list in README, which lists other departures from the brief, does not mention it. §13: "Silence about a gap is a defect."
- **Status:** open
