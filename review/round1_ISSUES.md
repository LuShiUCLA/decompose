# ISSUES: independent red-team review

Assessor: independent red-team session (no access to the builder's notes). Review date: 2026-11-22.
Clone reviewed: HEAD `f7553e5` ("README, licence, lockfiles, data notes, codebook excerpts, references; checksum warning").
Inputs: this repository, design brief §5 (reference values, survey/variable rules), §10–§13 (assessor checklist, definition of done).
How each finding was checked is in `VERIFICATION_LOG.md`. Severity scale: **blocker** (a §11 box cannot be ticked), **major** (wrong or misleading statistics/teaching, or a required deliverable missing), **minor** (local inaccuracy, unverifiable claim, or pedagogy defect).

Summary: 1 blocker, 6 major, 16 minor (23 findings). All open.

Reproduction snippets below assume Python 3.13, the repo's `programs/lib` on `sys.path`, and `a = nschlc_prepare.prepare("data/nschlc_2024_puf.dta")`.

---

## RT-001 — The §5.2 headline decomposition DOES essentially reproduce from the PUF; the repo's "does not reproduce" verdict is wrong and the lab teaches a different specification

- **Severity:** blocker (§11 box 1: headline must reproduce §5.2 within ±0.05 pp; the stated justification for not doing so is false)
- **Location:** `data-notes/reconciliation.md` lines 16–25 and 27 (n, gap, explained, unexplained, share, blocks, sensitivity); `README.md` lines 47 and 67–70; `lab/source.html` ("Fourteen did not reproduce … The full table, with the reason for each discrepancy"); `programs/lib/nschlc_prepare.py` lines 112–119 (CAREGIVER_POOR_MH); `programs/lib/nschlc_prepare.R` (same rule).
- **Steps to reproduce:**
  1. Keep every recode in `nschlc_prepare.py` except `CAREGIVER_POOR_MH`. Replace it with caregiver 1 only:
     `mh = A1_MENTHEALTH_W1.map({1:0,2:0,3:0,4:1,5:1})` (missing stays missing).
  2. Run `pooled_decomposition(a, des, "ADHD_EVER_W2", primary, P.BLOCKS, lv)` from `programs/core/decomposition_lab_core.py` (six implicates, Rubin).
  3. Repeat with `access = [INSURED_W2, USUAL_SOURCE_W2]` (preventive visit omitted).
- **Expected (brief §5.2):** n = 13,103; gap 9.67; explained 8.91; unexplained 0.76; blocks 3.37 / 2.19 / 2.43 / 0.64 / 0.28; sensitivity n = 13,143, gap 9.66, explained 8.86.
- **Actual with the one-line change (assessor run):** n = **13,102**; gap **9.65**; explained **8.97**; unexplained **0.68**; concentration+fidget **3.37**; other attention **2.24**; demographics **2.45**; access **0.64**; persistence/homework/calm **0.27**; sensitivity n = **13,142**, gap 9.65, explained 8.91 (implicate 1). The 40-row difference between primary and sensitivity samples is preserved exactly (brief 13,143 − 13,103 = 40; here 13,142 − 13,102 = 40). Taylor CIs: gap (5.48, 13.83), explained (4.47, 13.47), demographics (−0.74, 5.63).
- **Actual in the repo:** the lab teaches n = 12,977, gap 9.77, explained 8.19 (83.8%), unexplained 1.58, and tells readers the brief's figures "do not reproduce from the public-use file or from any logged run" (README) and were "checked against the logged runs and the public-use file" (Sources page). The repo's caregiver-mental-health rule (both caregivers must be observed unless `A2_RELATION = 8`) drops 308 children; caregiver-1-only drops far fewer. No search for the specification difference was done, and `reconciliation.md` gives no reason for most "does not reproduce" rows despite the Sources page saying it does.
- **What is needed:** decide which caregiver-MH rule is the study's (the brief's numbers point to caregiver 1 only, within one child), reproduce §5.2 within ±0.05 pp or document the residual one-child/0.06 pp difference as a justified methods difference, and correct README, `reconciliation.md`, the Sources page and the reproduce checker accordingly. The remaining 1-row difference was not resolved by the assessor.
- **Status:** open

## RT-002 — PSC rows of §5.2 reproduce exactly under the brief's own scoring rule; the repo marks them "does not reproduce"

- **Severity:** major
- **Location:** `data-notes/reconciliation.md` lines 29–30; `programs/lib/nschlc_prepare.py` line 108 (`PSCATT = PSCATT_W2`); Module 1/3 descriptives do not mention the scoring choice.
- **Steps:** compute the score as the brief §5.4 states (sum of (value − 1) over the five items, complete items only): `sc = sum(PSCx_W2_C for x in items)` (NaN if any item missing), then `des.mean(sc, primary & group, proportion=False)` and `des.mean((sc>=7), …)`.
- **Expected (brief):** mean 2.40 vs 1.54; ≥7: 8.6% (7.4, 9.8) vs 3.6% (1.4, 8.7).
- **Actual (assessor):** 2.398 vs **1.535**; ≥7 English 8.564 (7.435, 9.847), other **3.615 (1.448, 8.734)** — every figure matches the brief at its stated precision. The repo uses the Census-released `PSCATT`, which scores item nonresponse (.M) as 0 (Variable List), giving 1.50 and 8.53 (7.40, 9.80) / 3.58 (1.47, 8.49).
- **Fix:** mark these rows "reproduces (scoring rule differs)", and say in the lab which of the two scoring rules is used and why.
- **Status:** open

## RT-003 — Skip-count reconciliation is wrong and the Module 4 quiz states a false count

- **Severity:** major (factually false statement in the core Trap-1 lesson; §5.4 count misjudged)
- **Location:** `data-notes/reconciliation.md` line 34 ("12 does not (13)"); `lab/assets/quizzes.js` line 66 (`m4-a`, correct-option feedback); `programs/lib/nschlc_prepare.py` lines 85–88 (comment vs code).
- **Steps:** among ages 6–17, count `S4Q01_W2` missing: 13. Of those, `K4Q20R_W2` is answered for 1 child (value 1), and the code keeps that answer (line 87 maps K4Q20R before the S4Q01 rule). Count of `PREVENTIVE_W2` missing at ages 6–17: **49 = 37 + 12**.
- **Expected:** brief §5.4: "Only S4Q01-missing skips and K4Q20R-missing-despite-S4Q01 = 1 stay missing (… 37 arbitrary nonresponse; 12 S4Q01-missing)". 12 is exactly the number of S4Q01-missing children whose preventive indicator stays missing.
- **Actual:** reconciliation says the brief's 12 is wrong; quiz m4-a tells the learner "Only children whose S4Q01 is itself missing (13) or who had a visit but no K4Q20R answer (37) stay missing" — that sums to 50, but 49 stay missing. The prepare.py comment "S4Q01 missing/unknown stays missing" contradicts the code for that one child.
- **Status:** open

## RT-004 — Decomposition intervals are Taylor, not the PSU bootstrap the brief specifies; the deviation is undisclosed and distorts the reconciliation

- **Severity:** major
- **Location:** `programs/core/decomposition_lab_core.py` lines 129–147 (Taylor CIs reported as primary) and 234–264 (bootstrap as cross-check); Module 3 quiz `m3-c` ("the bootstrap here is a cross-check"); Module 5 table header "95% CI, Taylor"; `README.md` "Changes from the design brief" (no entry); `data-notes/reconciliation.md` lines 21 and 25.
- **Expected:** brief §5.3: "Decomposition standard errors: bootstrap resampling PSUs within strata (never children), 200 replicates, seed 20261117." Any departure listed with a reason.
- **Actual:** primary decomposition CIs are Taylor; this is not listed among the changes from the brief. The brief's CIs are narrower than Taylor in the way a bootstrap is (e.g. brief gap half-width 4.12 pp vs repo Taylor 4.25 and repo bootstrap 4.04), so `reconciliation.md` marks "global symptoms 3.37 vs 3.38" and "concrete covariates 0.28 vs 0.26" as "does not reproduce" although the point estimates agree within ±0.05 pp; the failures are CI limits computed by a different estimator.
- **Status:** open

## RT-005 — Exercise A attributes the LPM-vs-Fairlie difference to the model when it is mostly a change of reference coefficients

- **Severity:** major (mislabelled quantity; teaches a wrong conclusion)
- **Location:** `programs/lib/labsvy.py` lines 348–371 (`fairlie(..., coef="pooled")`: pooled logit **without** a group indicator); `programs/exercise-a/exercise_a_access_gap.py` line 115; `lab/exercises.html` results tables and note ("Fairlie uses pooled logit coefficients and matches children … (Fairlie, 2005)"); `lab/assets/quizzes.js` line 96 (`exa-1`).
- **Steps (implicate 1, spec A):** for USUAL_SOURCE_W2 compute (i) LPM English reference, (ii) Fairlie with `coef="A"` (English logit), (iii) Fairlie pooled (repo), (iv) LPM with pooled coefficients and no group dummy.
- **Actual (assessor):** usual source: LPM English **7.24**, Fairlie English **7.39**; LPM pooled-no-dummy **12.35**, Fairlie pooled-no-dummy **12.59**. Preventive: LPM English 13.17 vs Fairlie English 15.11; Fairlie pooled 11.50 vs Fairlie pooled+dummy 11.31.
- **Expected:** a like-for-like comparison (same reference) or an explicit statement that the two columns differ in reference as well as model. Module 2's own switcher text says the pooled option "includes a group indicator so the group difference is not absorbed into the slopes"; the Fairlie pooled model omits it. The exercise table and quiz `exa-1` ("For usual source the two differ by more than a few points: a reason to report both") lead the learner to attribute a 5.3 pp difference (7.34 vs 12.66) to linear-vs-logit, when holding the reference fixed removes almost all of it. Also: the detailed Fairlie contributions use weighted-quantile matching, not Fairlie's (2005) random one-to-one matching; the page cites Fairlie (2005) for the procedure.
- **Status:** open

## RT-006 — Exercise B is missing, and the lab page shows an empty section without saying so

- **Severity:** major (§11 box 3 cannot be ticked; §13 "silence about a gap is a defect")
- **Location:** `programs/exercise-b/` (README only); `lab/exercises.html` `#exercise-b` (`<div id="exb-body"><!--EXB--></div>`, nothing fills it); `lab/index.html` Day 2 plan ("about 6 hours: Exercise A … and Exercise B").
- **Steps:** open `lab/exercises.html` at 375 px or 1280 px and scroll to "Exercise B"; follow the index link `exercises.html#exercise-b`.
- **Expected:** Exercise B programs (Python + R, dry run, self-check, falsification) per §11; until then, an in-place notice that it is in progress.
- **Actual:** heading only, empty card; no status text on the page. Noted as declared in progress by the caller; not built by the assessor.
- **Status:** open

## RT-007 — The "reference values", the risk-ratio model and the label corrections rest on a pipeline that is not in the repository

- **Severity:** major
- **Location:** `README.md` "Work that predates this lab"; `data-notes/logged_reference/*`; `data-notes/reference_values.json`; Module 5 "A longitudinal look" (RRs 0.23/0.13, E-values 8.04/15.08, n = 13,485); `data-notes/reconciliation.md` RR and "earlier specification" rows (cite `original/nsch-lc-adhd-language-gap-replication-2026-11-17.py`, not shipped).
- **Expected:** §10.1/§11: a stranger can regenerate every displayed number from the repo, and checks that compare against "reference values" are independent of the thing being checked.
- **Actual:** the self-check compares the lab's code to CSVs produced by code (`nsch_lc_adhd_language_gap.py`, `survey_engine.py`, …) stored in a private project folder. The modified-Poisson RRs and E-values are not computed by any shipped program (the page discloses this). The relabelling of the brief's RR 0.23 as "Spanish vs English" (brief: other-language vs English) and of 0.13 rests only on these CSVs. The assessor verified the E-value arithmetic from the logged RRs (8.04/3.32, 15.08/7.26) but could not verify the model or its labels. Note: the crude new-report ratio for all non-English households combined is 2.52/10.32 = 0.24, so the brief's label is not implausible on its face.
- **Status:** open

## RT-008 — Codebook excerpts omit variables the programs use and show the wrong education variable

- **Severity:** minor
- **Location:** `data-notes/codebook_excerpts.md` line 29; `data-notes/extract_codebook.py` line 14; `programs/lib/nschlc_prepare.py` lines 97–126.
- **Actual:** the excerpt lists `HIGRADE_TVIS` (4 categories) but the programs use `HIGRADE` (3 categories: <HS, HS, >HS). Rows for `K7Q84_R`, `A1_MENTHEALTH`, `A2_MENTHEALTH`, `A2_RELATION` (code 8 = only one caregiver, which drives the 308-child loss in RT-001) and `MEMORYCOND` are absent. The file claims to hold "the Variable List rows the lab relies on".
- **Status:** open

## RT-009 — Reproduce checker gives a diagnostic that cannot be the cause

- **Severity:** minor
- **Location:** `lab/assets/app.js` line 168.
- **Steps:** on `index.html` enter 9.67 / 8.91 / 0.76 (the brief's values) and press Check.
- **Actual:** "Check your sample first (n should be 12,977), then the PSC rescaling, then …". Shifting the PSC items from 1–3 to 0–2 cannot change any decomposition term (the repo's own comment, `nschlc_prepare.py` lines 104–105). Also "9.67 is 0.10 pp away" is shown as a failure of the ±0.1 pp bar (true difference 0.104); the rounded display contradicts the verdict.
- **Status:** open

## RT-010 — Sandbox Case C marks "No meaningful effect" wrong although the effect is 0.3%

- **Severity:** minor (pedagogy: penalises a correct judgement)
- **Location:** `lab/assets/interactions.js` lines 197–199; Module 3 sandbox.
- **Actual:** pre-subset SE 1.813 vs domain 1.818 pp (0.3%); the feedback for the "correct" option itself says "the difference is tiny". Choosing "No meaningful effect" yields "Not yet". The direction is correct, but the option labels make the right magnitude judgement wrong.
- **Status:** open

## RT-011 — Sandbox step 1 prediction is never used; generic hint mentions n where n does not change

- **Severity:** minor
- **Location:** `lab/assets/interactions.js` lines 225–241.
- **Actual:** the "higher / lower / about the same" prediction is required but no feedback refers to it. After a wrong diagnosis every case appends "compare its n with the corrected analysis's n", which is irrelevant for Cases B and C (same n) and for D (n is the subject, not a clue).
- **Status:** open

## RT-012 — Quiz answer position is predictable

- **Severity:** minor
- **Location:** `lab/assets/quizzes.js` (all 22 items).
- **Actual:** the correct option is always the 1st or 2nd (13 and 9 items), never 3rd or 4th; options are not shuffled; the correct option is usually the longest. A test-wise learner can score well without the content.
- **Status:** open

## RT-013 — Writing checklists flag correct non-causal statements as causal

- **Severity:** minor
- **Location:** `lab/assets/quizzes.js` `WRITING.counterfactual` and `WRITING.exa` (`none: [" cause", "causes", …]`).
- **Steps:** in Module 1 write "This analysis does not mean that attention causes the gap …".
- **Actual:** "✖ Avoids causal language — You used ' cause'". The learner is corrected for writing the disclaimer the lab asks for.
- **Status:** open

## RT-014 — Seminar defence understates how many LPM predictions are out of range

- **Severity:** minor
- **Location:** `lab/assets/quizzes.js` line 126 (`seminar-3`).
- **Actual:** the feedback gives counts (2,557 English, 262 other-language, implicate 1) but not shares: 21% of English and 34% of other-language fitted values are outside [0, 1]. The "correct" defence calls it "a known limitation" without the scale.
- **Status:** open

## RT-015 — Exercise A circularity comparison is not same-case

- **Severity:** minor
- **Location:** `programs/exercise-a/exercise_a_access_gap.py` lines 198–201; `lab/assets/quizzes.js` `exa-2`.
- **Actual:** spec B changes the sample (preventive: n 13,564 → 13,584; gap 13.22 → 13.55), yet `exa-2` attributes the fall in explained (13.18 → 12.13) to removing the circular covariate. Module 5 (`m5-b`) teaches that only a same-case comparison isolates a covariate.
- **Status:** open

## RT-016 — Learning-science and citation claims that overreach or cannot be supported

- **Severity:** minor
- **Location:** `lab/why-this-lab-works.html`; `lab/modules/2-machine.html` (Interaction 3 "Why predict first"); `lab/modules/1-question.html` predict-bars feedback (`interactions.js` line 265); references lists.
- **Actual:**
  (a) Why page: Schultz, Dayan & Montague (1997) is cited "only to name where the term 'prediction error' comes from". The term predates it (Rescorla–Wagner 1972; temporal-difference learning). Citing a dopamine-neuron paper as the rationale in Module 2 also sits uneasily with §13's ban on neuroscience framing.
  (b) Cepeda et al. (2006) "Limit" column: "one night is a minimum, not an optimum" is not a finding of that review.
  (c) Renkl, Atkinson & Maier (2002), J. Exp. Educ. 70(4): to the assessor's knowledge the article has a fourth author (Staley). The assessor could not confirm this against Crossref from this environment.
  (d) Kornell, Hays & Bjork (2009) used verbal materials (word pairs, trivia). The page applies it to predicting a quantitative split without saying that this is an extrapolation.
  (e) Predict-bars feedback: "The biggest surprise for most people is …": an empirical claim with no data behind it.
- **Status:** open

## RT-017 — Time estimates presented without the "not measured" caveat in place

- **Severity:** minor
- **Location:** `lab/index.html` plan ("Day 1 … about 5–6 hours", "Day 2 … about 6 hours").
- **Actual:** README says the estimates are the builder's and not measured; the lab page does not say so (brief's iron rule: say so in place).
- **Status:** open

## RT-018 — Factual statements that cite Census documents not excerpted in the repo (unverifiable by the assessor)

- **Severity:** minor
- **Location:** Module 1 (telephone assistance in English, Spanish, Mandarin, Russian, Hindi, Portuguese); Module 3 (weights raked to the average of 2018 and 2019 ACS child estimates; S&A "pp. 6–7" design specification); `data-notes/README.md` (strata = `FIPSSTO` × `STRATUM`).
- **Actual:** the Methodology Report and S&A Statement are listed by checksum only; no excerpt is shipped, and census.gov is unreachable from the assessor's environment. The strata choice matters: `FIPSST` × `STRATUM` (the brief's wording) also gives 102 strata, but 928 children's 2024 state differs from their original state, so the two definitions differ. The `FIPSSTO` choice rests only on S&A text not in the repo.
- **Status:** open

## RT-019 — Unsupported or inaccurate claims in sandbox and programs README

- **Severity:** minor
- **Location:** `lab/assets/interactions.js` line 187; `programs/README.md` line 32.
- **Actual:** Case B feedback says the CURRCOV error is "not ignorable" for an access analysis; no program isolates CURRCOV's effect on an access decomposition (Exercise A spec C changes both traps at once). `programs/README.md` says insured rates "change in the second decimal"; the English rate moves 0.45 pp (96.91 → 97.36).
- **Status:** open

## RT-020 — Exercise A self-check is thin

- **Severity:** minor
- **Location:** `programs/exercise-a/exercise_a_access_gap.py` lines 163–185, 208–230; `exercise_a_access_gap.R`.
- **Actual:** there is no comparison against any independently logged value. The checks are the identities, one falsification test, and an R-vs-Python comparison in which R reads the committed Python JSON. The Fairlie dry run tests `coef="A"`, but the analysis uses `coef="pooled"`. A stale comment ("assign y in x-rank order") describes code that does not exist. No R run log is written for Exercise A.
- **Status:** open

## RT-021 — Brief requirements for the interactions met only partly

- **Severity:** minor
- **Location:** Module 3; Module 2 Interaction 3.
- **Actual:** §5.3 asks that "the lab's calculator show both" singleton-stratum conventions; Module 3 shows remove/adjust SEs as static text only. §5.3 asks that the learner "run the logit version"; Interaction 3 reveals precomputed numbers. (§6 of the brief was not provided to the assessor, so the full §6.3 interaction list could not be checked.)
- **Status:** open

## RT-022 — Bootstrap teaching claims a clustering benefit that does not exist in this design

- **Severity:** minor
- **Location:** `programs/lib/labsvy.py` lines 331–334 (docstring); `programs/core/decomposition_lab_core.py` line 252 comment; Module 3 "Children are never resampled one by one"; quiz `m3-b` correct-option feedback ("preserves clustering").
- **Actual:** PSU = household with exactly one sampled child (21,768 PSUs = 21,768 children), so resampling PSUs and resampling children are identical here. Only stratification matters. The docstring's claim that resampling children "would ignore clustering and understate the SE" does not apply to this file. Quiz `m3-b`'s wrong-option feedback states this correctly, so the lab contradicts itself.
- **Status:** open

## RT-023 — Reconciliation and Sources page overstate what was checked

- **Severity:** minor (consequence of RT-001–RT-004)
- **Location:** `lab/source.html` ("Fourteen did not reproduce … Each was checked against the logged runs and the public-use file … with the reason for each discrepancy"); `data-notes/reconciliation.md`.
- **Actual:** at least 9 of the 14 "did not reproduce" rows reproduce, or nearly reproduce, under a documented alternative choice: the caregiver-MH rule (RT-001), the brief's PSC scoring rule (RT-002), the skip-count definition (RT-003) or the bootstrap CI (RT-004). Most rows have no stated reason.
- **Status:** open
