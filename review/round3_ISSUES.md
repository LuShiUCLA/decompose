# ISSUES: independent red-team review, round 3

Assessor: independent red-team session (no access to the builder's notes). Review date: 2026-11-22.
Clone reviewed: HEAD `052d444` ("Fix red-team round 2: brief figures reproduce exactly (brief_method), checker negation, quiz length cues, Exercise B R log").
Scope: re-verify the 9 items open after round 2 (RT-012, RT2-001 … RT2-008) and look for defects introduced by the round-3 changes. Round-1 items closed in round 2 are not re-listed. Evidence and commands are in `VERIFICATION_LOG.md`. Severity scale as before: **blocker** (a §11 box cannot be ticked), **major** (wrong or misleading statistics or teaching), **minor** (local inaccuracy or pedagogy defect).

**Summary.** Of the 9 open items, 8 are closed and 1 is still open (RT2-003, major). 1 new finding (RT3-001, minor). No blockers.

## Status of the items open after round 2

| ID | Status | Evidence (one line) |
|---|---|---|
| RT-012 | closed | The correct option is now the longest in 6 of 25 items (was 23); positions are spread over 1st–4th. I read the rewritten options: each correct one is still correct and each distractor is still wrong. |
| RT2-001 | closed | `brief_method()` (Python) gives n 13,103; gap 9.67 (5.55, 13.78); explained 8.91 (4.56, 13.25); unexplained 0.76 (−3.55, 5.07); all five blocks and the no-preventive row match the brief to ±0.005 on point and both limits (139 PASS, 0 FAIL). R checks the points (131 PASS) and says why it does not check the limits (different RNG). README, Sources page, reconciliation and Module 5 now describe the method correctly. |
| RT2-002 | closed | The reconciliation marks the 11,928 specification "reproduces (superseded first program)" and the all-ages row "gap and explained reproduce; n does not"; the points in the shipped log equal my round-2 run of the same program. Two loose ends: RT3-001. |
| RT2-003 | **still open** | The reported pattern is fixed ("Access, not symptoms, causes the gap" is now flagged). New tests in all four checklists still let causal claims through and still flag correct disclaimers; see below. |
| RT2-004 | closed | README, `census_excerpts.md` and the reconciliation now say Wave-1 `FIPSST` equals `FIPSSTO` for every child. The Methodology Report p. 38 sentence now quoted is verbatim, and the page says what p. 38 does not contain. |
| RT2-005 | closed | A text with no gap or interval but "special health care needs" now gets "✖ Reports the gap with its interval" and "✖ compatible with no gap". Robustness keywords are specific. |
| RT2-006 | closed | The R program writes `output/exercise_b_run_log_R.txt` and recomputes and cross-checks the sample flow, ESS and largest weight share; page wording now matches. Re-run in this review: see `VERIFICATION_LOG.md` §3. |
| RT2-007 | closed | README and `pipeline/README.md` now say the shipped copy is a later revision (216 vs 175 and 185 vs 157 rows, variance scale, descriptive columns) that reproduces every shared estimate; this matches my round-2 re-run. |
| RT2-008 | closed | README "Changes from the design brief" now has a "Prediction-error principle" entry with the reason. |

---

## RT2-003 (still open) — The causal-language check still passes causal claims and flags correct disclaimers

- **Severity:** major (§13: the learner is corrected every time they use causal language. The check now gets both directions wrong on ordinary sentences.)
- **Location:** `lab/assets/app.js` `checklist()`. A flagged word is excused when one of the `NEG` phrases (does not, cannot, is not, …) appears among the 7 words before it, after cutting the text at `.!?;,:`.
- **Steps to reproduce (`pw_check2.js`, headless Chromium):** on Module 1, enter the counterfactual sentence followed by each test sentence, then press "Get checklist feedback".
- **Expected:** causal claims get "✖ Avoids causal language" and disclaimers get "✔".
- **Actual, causal claims that pass ("✔"):**
  - "It is not surprising that access causes the gap."
  - "We do not doubt that language barriers cause the gap."

  The negated verb does not govern "causes", but it is within 7 words.
- **Actual, correct disclaimers that are flagged ("✖ … You used " cause""):**
  - "It does not show that symptoms, rather than access, cause the gap." The comma cuts the clause before the negation.
  - "Nothing here shows what causes the gap." "Nothing" is not in the list.
  - "We cannot conclude from an accounting exercise that measured symptoms cause the gap." The negation is 9 words away.

  Round 1's sentence ("This does not mean that attention causes the gap") and round 2's contrastive cases are now handled correctly.
- **Note:** a keyword checker cannot parse negation scope reliably. A fix that holds is to stop scoring this item as pass/fail. Instead, list every causal verb found, quote its sentence, and ask the learner to confirm that each one is negated. Then neither failure mode can mislead.
- **Status:** open

## RT3-001 — The shipped log of the original program's sections E/F hides a 2-replicate run, and it contains the "18,042" the reconciliation says was not found

- **Severity:** minor
- **Location:** `data-notes/logged_reference/original_program_sections_EF_run.log`; `data-notes/reconciliation.md` row "All-ages Tier 2 Oaxaca" ("the source of 18,042 was not found"); `lab/source.html` ("on 21,204 children rather than the 18,042 the brief states"); `programs/core/decomposition_lab_core.py` docstring of `brief_method()` ("sections A-D").
- **Actual:**
  - (a) **2-replicate run.** Every block in the log says "bootstrap replicates kept: 2/2", and its intervals come from 2 replicates. Section F primary explained shows (6.20, 7.81), but a 200-replicate run of the same program gives (1.42, 12.59). Neither the log, the reconciliation nor any README gives the command line or says the run used `--n-boot 2`. Only the points are quoted, and those are correct and equal my 200-replicate run (10.90 / 5.02; 8.78 / 7.00). But a reader of the log would take its intervals at face value.
  - (b) **The 18,042 is in the shipped log.** Line 84 reads `=== sensA_allages_psconly: complete-case n=18,042 (input n=21,481) ===`. So the brief's "All-ages Tier 2 (n = 18,042): gap 10.90, explained 5.02" pairs Section E's estimates with the n of Section F's all-ages sensitivity (whose own gap and explained are 9.64 and 5.67). The reconciliation and Sources page say the source was not found.
  - (c) **Wrong section label.** The `brief_method()` docstring says the method is in the original program's "sections A-D". The bootstrap it copies is the decomposition routine (`oaxaca_blinder`, file section 8) used by sections E and F. Sections A–D are other analyses.
- **Expected:** the log has a header with the command and replicate count (or is re-run with the default 200). The 18,042 row names its source. The docstring points to `oaxaca_blinder`.
- **Status:** open
