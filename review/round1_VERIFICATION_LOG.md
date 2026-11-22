# VERIFICATION LOG: independent red-team assessment (round 1)

Date: 2026-11-22. Assessor: independent session with no access to the builder's notes, drafts or reasoning. Inputs were limited to this repository clone, the design brief's §5 (reference values, survey and variable rules) and §10–§13 (assessor instructions, definition of done, structure, constraints). The brief's §6 (interactions) and §9 (learning-science requirements) were **not** provided, so compliance with those sections was not checked except where §10–§11 refer to them.

**Sign-off status: NOT signed off.** 23 findings are open (1 blocker, 6 major, 16 minor); see `ISSUES.md`. Under §10.2 the lab cannot ship until they are closed and re-verified.

---

## 1. Environment

| Item | Value |
|---|---|
| OS | Linux 6.18 (container) |
| Python | 3.13.18; numpy 2.2.6, pandas 2.3.0, scipy 1.15.3 (matches `programs/requirements-lock.txt`) |
| R | 4.3.3 (2024-02-29); survey 4.2.1, haven 2.5.4, jsonlite 1.8.8 (matches `programs/R-packages.lock`) |
| Browser | Playwright + headless Chromium (Node v22.23.5) |
| Network | census.gov, doi.org and crossref.org **not reachable**. Data were not downloaded from the §5.1 URLs; the PUF was pre-placed in `data/`. |
| Clone | HEAD `f7553e5`; working tree clean before the runs |

## 2. Data checksum

| File | SHA-256 (assessor) | Documented in `data-notes/README.md` | Result |
|---|---|---|---|
| `data/nschlc_2024_puf.dta` (31,316,899 bytes) | `d483c989262b2ce4a36173b2e7fd63d2a3edfddaa1b7ef2372ff8abcd99799ce` | same | **match** |
| `data-notes/sources/NSCH-LC-Variable-List.xlsx` | `1bd036cc2eb45f5841844cc4c0c7447e68a0d91c7abc4f6f36fd8999e3429ae7` | same | **match** |
| `nschlc_2024_puf_Stata.zip` | not available | `02200328…` | **not verified** (zip not present; Census not reachable) |
| Methodology Report, S&A Statement, FAQs, imputed-data guide, questionnaire | not in repo | checksums in `documentation_manifest.json` | **not verified** |

Release checks in `prepare()` passed: 43,536 rows, 21,768 unique HHID, 102 strata, design df 21,666.

## 3. Programs re-run (from the clone root)

| # | Command | Exit | Wall time | Key output | Self-check |
|---|---|---|---|---|---|
| 1 | `python programs/core/decomposition_lab_core.py` | 0 | 22.6 s | synthetic dry run PASS; n = 12,977; gap 9.77 (5.52, 14.03); explained 8.19 (3.64, 12.74); unexplained 1.58 (−2.95, 6.11); bootstrap gap (5.73, 13.82) | **93 PASS, 0 FAIL** |
| 2 | `Rscript programs/core/decomposition_lab_core.R` | 0 | 34.8 s | same points; R bootstrap gap (5.75, 13.80); survey-pkg SE = hand SE (24 checks, tol 1e-6) | **105 PASS, 0 FAIL** |
| 3 | `python programs/exercise-a/exercise_a_access_gap.py` | 0 | 44.9 s | preventive A: gap 13.22, LPM explained 13.18, Fairlie 11.51 (7.39, 15.63); usual source A: gap 21.85, LPM 7.34, Fairlie 12.66 | 5 PASS, 0 FAIL (+2 INFO) |
| 4 | `Rscript programs/exercise-a/exercise_a_access_gap.R` | 0 | 128 s | R matches Python to ≤5e-12 on every LPM and Fairlie point estimate | 46 PASS, 0 FAIL (+4 INFO: bootstrap CI limits differ 0.10–0.20 pp because the two languages use different RNGs) |
| 5 | `python programs/build_lab_data.py` | 0 | <1 s | wrote `lab/assets/lab-data.js` (77 KB) | n/a |
| 6 | `python lab/_src/build_site.py` | 0 | <1 s | built 9 pages + `why-this-lab-works.md` | n/a |

**Comparison with committed outputs:** after runs 1–6, `git status` showed **no changes**. All committed outputs (`core_results*.json`, run logs, Exercise A JSON/log, `lab-data.js`, built HTML) are byte-identical to the re-run. The re-run matches the logged reference outputs exactly, bootstrap included, for the same seed and versions.

**Not run:** Exercise B (absent; declared in progress; see RT-006). No clean-room install from the lockfiles was done; the preinstalled packages already had the locked versions. The automatic download path in `obtain()` was not tested (no network).

## 4. Reference values: §5.2 versus the repo, and the assessor's independent check

Assessor scripts were run outside the repo against `programs/lib/nschlc_prepare.py` and `labsvy.py`.

| §5.2 quantity | Repo verdict | Assessor finding |
|---|---|---|
| 21,768 interviews | reproduces | confirmed (PUF row and HHID counts). The 43.0% response rate was not verified (Methodology Report not available). |
| Incident ADHD E/Sp/Other/non-English | reproduces | confirmed: 10.32 (9.02, 11.78), 2.99 (1.48, 5.94), 1.14 (0.58, 2.21), 2.52 (1.35, 4.66) |
| 16.3% vs 6.0% "at Wave 1" | label wrong (Wave 2) | **confirmed repo is right**: the Wave 1 rates are 12.27% vs 4.74% (ages 6–17 at baseline). The Wave 2 rates are 16.29% vs 5.97%. |
| RR 0.23 / 0.13, E-values | label wrong | E-value arithmetic confirmed from the logged RRs: 8.04 (3.32) and 15.08 (7.26), using the CI limit closest to 1. The model and the Spanish/other labels could **not** be verified: the producing code is not in the repo (RT-007). |
| Decomposition n, gap, explained, unexplained, share, blocks, sensitivity | does not reproduce | **Repo verdict rejected.** With caregiver-1-only mental health, the spec gives n = 13,102 (brief 13,103), gap 9.65, explained 8.97, unexplained 0.68, blocks 3.37/2.24/2.45/0.64/0.27, and sensitivity n = 13,142 with explained 8.91 (RT-001). |
| Global symptoms / concrete covariates blocks | does not reproduce | points agree within 0.05 pp; the "failure" comes from comparing Taylor CIs with the brief's (apparently bootstrap) CIs (RT-004) |
| Earlier spec (n = 11,928) and all-ages Tier 2 (n = 18,042) | does not reproduce | **not reproduced by the assessor either** (tried strict and caregiver-1 MH rules, total score and items, all ages: n = 19,988–20,483). Repo verdict not contradicted. |
| PSC mean 2.40 vs 1.54; PSC ≥ 7 | does not reproduce | **Repo verdict rejected**: the brief's §5.4 rule (sum of item − 1, complete items) gives 2.40 vs 1.54 and 8.6 (7.4, 9.8) vs 3.6 (1.4, 8.7) exactly (RT-002) |
| Usual source, CURRINS, preventive | reproduce | confirmed |
| Skip counts 1,249 / 37 / 12 | "12 does not (13)" | **Repo verdict rejected**: 12 S4Q01-missing children stay missing; 1 more answered K4Q20R (RT-003) |
| CURRINS vs CURRCOV: 65 | reproduces | confirmed: all 65 are CURRINS = 2 and CURRCOV = 1, so CURRCOV overstates insurance; the lab states this direction correctly |
| Strata: 102 | reproduces (FIPSSTO) | confirmed 102 with FIPSSTO; FIPSST also gives 102 but different strata (928 movers); the S&A basis was not verified (RT-018) |
| Model n vs design-matrix n | n/a | confirmed: 13,021 − 44 = 12,977 |

## 5. Statistics checked

- **Survey design:** FWC weight, strata FIPSSTO×STRATUM (2A→2), PSU HHID; Taylor with-replacement variance from PSU totals of influence values with n_h/(n_h−1). Code reviewed (`labsvy.py` lines 36–117, `labsvy.R`). The R hand-coded SEs equal `survey::svymean` to 1e-6 (24 checks). The "adjust" lonely-PSU implementation equals R `survey` "adjust" (1.813524 in both).
- **Domain estimation:** zero influence outside the domain; full-design df. Correct. Pre-subset vs domain SE: 1.813 vs 1.818 pp (0.3%). The direction (understates) is correct but the effect is negligible here; the lab says so (see RT-010).
- **Decomposition algebra:** explained = (x̄E − x̄O)′bE and unexplained = x̄O′(bE − bO) are checked as identities in code (assert, 1e-10). The influence functions use the product rule over the mean and WLS-coefficient influences, which is correct. Reference variants (other, pooled with a group dummy, threefold from Jann's group-B viewpoint) are correct.
- **Rubin pooling:** T = W + (1 + 1/m)B with Barnard–Rubin df. Formula verified line by line.
- **Bootstrap:** Rao–Wu rescaled, n_h − 1 draws per stratum, 200 replicates, seed 20261117, Rubin-combined, normal 1.96 CI. Correct, but used only as a cross-check (RT-004). Because each household has one child, the "never resample children" point is vacuous for this file (RT-022).
- **Trap 1 (K4Q20R):** structural-zero coding verified. Dropping skips raises the other-language rate 72.76 → 98.85% and English 85.99 → 97.17%, which reverses the preventive-visit gap (Exercise A spec C: −1.68 pp). The stated direction of bias (up) is correct.
- **Trap 2 (CURRINS):** verified. The stated direction (CURRCOV higher) is correct. The effect on the ADHD decomposition is in the 4th decimal (8.1937 vs 8.1935), as the lab says.
- **Logit vs LPM:** the naive at-means logit leaves a 2.88 pp residual; the average-prediction logit and the LPM leave 0 (verified in output). A full-covariate logit fails to converge in the other-language group (assessor run: perfect prediction, 0 events in race codes 3 and 7), so the reduced set is justified.
- **Fairlie:** aggregate and all-orderings Shapley-style averaging verified (block means sum to the aggregate). Problems: no group dummy in the pooled logit, and a reference that differs from the LPM's (RT-005). Matching is weighted-quantile, not Fairlie's.
- **Causal language:** every module page and the exercises carry a "Compositional, not causal" box on the results screens. No causal overclaim was found in the text. The checklists over-flag (RT-013).

## 6. Lab click-through (headless Chromium, `file://`)

Pages: index, modules 1–5, exercises, why-this-lab-works, source, each at **1280×900 and 375×740**.

| Check | Result |
|---|---|
| Console errors / page errors | 0 on all 18 page loads, and 0 during the interaction runs |
| Network requests other than `file:`/`blob:` | **0** (no fonts, CDNs or analytics) |
| Displayed placeholders (`[missing`, `n/a`, `NaN`, `undefined`, `{{`) | 0. Every `data-num`/`data-ci` element is filled. |
| Horizontal overflow at 375 px | 0 px on all pages (tables scroll inside `.tablewrap`) |
| Internal links (files and `#anchors`) | all resolve; 0 broken |
| Form controls without labels | 0 |
| Quizzes | all 22 items: every option clicked and checked, plus a no-selection submit. Feedback rendered for each with numbers filled. Truth checked against outputs: false statements in `m4-a` (RT-003); misleading `exa-1` (RT-005), `exa-2` (RT-015), `seminar-3` (RT-014). All others are consistent with program output. |
| Sandbox | 4 cases × every error × direction combination (52 submissions) plus empty submits. The correct combination is accepted in each case and the corrected output is revealed. Issues: RT-010, RT-011. |
| Calculator | 5 blocks × scale 0/100/300%: the gap stays fixed and explained + unexplained = gap |
| Reference switcher | 4 variants; values match `core_results.json`; `aria-pressed` updates |
| Logit vs LPM | requires a prediction; both predictions give correct feedback; table matches output |
| Faded examples / rebuild | correct, near-miss, proportion, sign-flipped and non-numeric inputs give the intended diagnostics |
| Predict-the-split sliders | work by mouse and keyboard; sum updates; reveal works |
| Reproduce checker | correct values pass; proportions, other-reference and dropped-skip inputs get specific diagnoses; empty input is handled. Issue: RT-009. |
| Writing checklists | short-text guard works; checklist and model answer appear; RT-013 |
| Exporter | own `core_results.json` loads locally; invalid, garbage and partial JSON give an error status; download `decomposition_table.md` produced |
| Exercise B section | **empty** (RT-006) |
| Keyboard-only | skip link works; tab order is logical; visible 3 px focus outline; quiz answered with arrows/Space/Enter; reproduce checker by Tab/Enter; slider by arrows/End; switcher by Enter; sandbox by Space/Enter |
| localStorage blocked | page works, no errors |

## 7. Citations

DOI resolution **was not possible from this environment** (doi.org and crossref.org unreachable). All 26 DOIs in `references/references.md` and on the pages were checked for **internal consistency and against the assessor's own knowledge only**. Each DOI is consistent with the cited article. Possible author omission: Renkl et al. (2002) (RT-016c). The design brief's Cepeda DOI correction (`10.1037/0033-2909.132.3.354`) agrees with the assessor's knowledge. The claim-versus-source review of the learning-science table found the overreaches listed in RT-016; the remaining rows paraphrase their sources fairly, and the "Limit" column is a good practice. The methods citations (Oaxaca, Blinder, Jann, Fairlie, Fortin et al., DiNardo et al., Rao & Wu, Lumley, VanderWeele & Ding, Sinning et al.) are attached to claims consistent with those works, except the attribution of the matching procedure to Fairlie (2005) (RT-005).

## 8. What the assessor could NOT verify

- Downloading from the §5.1 URLs, the zip checksum and whether those URLs are current (no network).
- Any statement sourced to the Methodology Report, the Source and Accuracy Statement, the FAQs or the imputed-data guide: response rate 43.0%, interview languages, raking controls, the FIPSSTO strata specification and the Taylor/with-replacement prescription (documents not in the repo).
- The modified-Poisson risk-ratio model and its labels, and the "reviewed pipeline" that produced `data-notes/logged_reference/` (code not in the repo).
- The remaining one-child difference between 13,102 and the brief's 13,103 (RT-001), and the brief's 11,928 and 18,042 specifications.
- DOI resolution and Crossref metadata for every reference.
- Brief §6 (interactions) and §9 (learning-science requirements), which were not provided.
- Exercise B (not built).
- A clean install from the lockfiles (versions were already present) and phone hardware (only a 375 px emulated viewport).

## 9. Statement

Every command in §3 was run by the assessor in this clone, and each figure above is taken from the assessor's own runs or code reading. The programs run, agree across Python and R, and reproduce their committed outputs exactly. The web lab is static, makes no network requests, works at 375 px and keyboard-only, and shows no missing numbers. However, the repository's central claim that the brief's headline figures cannot be reproduced from the public-use file is contradicted by the assessor's runs (RT-001 to RT-003), and Exercise B is absent. **Not signed off.**
