# VERIFICATION LOG: independent red-team assessment (round 3)

Date: 2026-11-22. Assessor: independent session with no access to the builder's notes. Inputs: this clone (HEAD `052d444`), the design brief, the round-2 `ISSUES.md` and the assessor's own round-2 scratch runs (including a 200-replicate run of the shipped original program, sections E and F up to the primary specification).

**Sign-off status: NOT signed off.** Of the 9 items open after round 2, 8 are closed and 1 is still open (RT2-003, major). One new minor finding (RT3-001). See `ISSUES.md`.

## 1. Environment

The same as round 2: Python 3.13.18 (numpy 2.2.6, pandas 2.3.0, scipy 1.15.3), R 4.3.3 (survey 4.2.1, haven 2.5.4, jsonlite 1.8.8), Playwright with headless Chromium on Node v22.23.5. The data are the same symlinked files, with checksums verified in round 2. The clone was clean before the runs.

## 2. What changed (`git diff --stat 6e10413 052d444`)

There are 25 files. The main ones are:
- `programs/core/decomposition_lab_core.py` (+`brief_method()`) and `.R` (brief-method points).
- `lab/assets/app.js` (negation guard, reproduce-checker branch) and `lab/assets/quizzes.js` (option rewording, Exercise B keywords).
- Module 5, Sources and Exercises pages.
- `data-notes/reconciliation.md` and `make_reconciliation.py`.
- A new `data-notes/logged_reference/original_program_sections_EF_run.log`.
- `census_excerpts.md`, README notes, the Exercise B R program and its new R run log.

## 3. Programs re-run (from the clone root)

| # | Command | Exit | Time | Key output | Self-check |
|---|---|---|---|---|---|
| 1 | `python3 programs/core/decomposition_lab_core.py` | 0 | ~50 s | headline unchanged (n 12,977; 9.77 / 8.19 / 1.58). `brief_method`: n 13,103, gap 9.67 (5.55, 13.78), explained 8.91 (4.56, 13.25), unexplained 0.76 (−3.55, 5.07). No-preventive: n 13,143, 9.66 (5.56, 13.76), 8.86 (4.53, 13.20) | 139 PASS, 0 FAIL (32 brief-method checks at ±0.005, limits included) |
| 2 | `Rscript programs/core/decomposition_lab_core.R` | 0 | ~40 s | brief method (points): 9.67 / 8.91 / 0.76; no-preventive 9.66 / 8.86 | 131 PASS, 0 FAIL |
| 3 | `Rscript programs/exercise-b/exercise_b_care_navigation.R` (the Python output was unchanged, so it was not re-run) | 0 | 6 min 8 s | the run log now has the sample flow, ESS 156 and largest share 0.0465 | cross-check 80 PASS, 0 FAIL (includes the 6 sample-flow steps, ESS and largest weight share) |
| 4 | `python3 programs/build_lab_data.py` | 0 | <1 s | `lab-data.js` 106 KB | n/a |
| 5 | `python3 lab/_src/build_site.py` | 0 | <1 s | 9 pages + `.md` | n/a |

**git diff check:** after runs 1–5, `git status` shows only the assessor's `ISSUES.md` (and later this file). Every regenerated output is byte-identical to the committed one, including the new R Exercise B run log and both core run logs.

## 4. Specific verifications

- **RT2-001.** I compared the `brief_method()` code with my round-2 `boot_probe.py`. It uses the same steps: earlier rule, implicate-mean income, the 13,607 analysis rows, strata in order of first appearance, `rng.choice` of n_h rows, SD × 1.96. Its output equals the brief and my round-2 numbers to two decimals. The prose was checked against `core_results.json`:
  - The Module 5 "Three choices" table renders 12,977 / 9.77 (5.52, 14.03) / 8.19 (3.64, 12.74), then 13,103 / 9.67 (5.49, 13.84) / 8.89 (4.38, 13.40), then 13,103 / 9.67 (5.55, 13.78) / 8.91 (4.56, 13.25).
  - "Demographics 1.73 → 2.41" and "most of a point" (0.70) are correct.
  - The statement that unrescaled n_h draws understate variance is correct: the naive bootstrap variance carries a factor (n_h−1)/n_h.

  The Sources page bullet and the reconciliation rows (all "reproduces exactly (brief method)", explained share 92.1%) match.
- **Reproduce checker.**
  - Entering 9.67 / 8.91 / 0.76 gives the "design brief's figures" diagnosis on all three fields.
  - Entering 9.67 / 8.89 / 0.78 gives the brief diagnosis on the gap (9.67 is within 0.01 of both runs) and the earlier-rule diagnosis on the other two.

  Both are correct.
- **RT2-002 / RT3-001.** The shipped EF log was compared with my round-2 200-replicate run of the same program:
  - Point estimates are identical: Section E 10.896732 / 5.015404 / 5.881328; Section F primary 8.781804 / 7.002391 / 1.779413, n 11,928.
  - The intervals differ because the shipped log says "bootstrap replicates kept: 2/2" in every block. For example, the primary explained interval is (6.20, 7.81) in the shipped log and (1.42, 12.59) in my run.
  - Line 84 of the shipped log has `sensA_allages_psconly: complete-case n=18,042`.
- **RT2-003.** `pw_check2.js` ran 14 cases.
  - Causal claims that should be flagged:
    - Correctly flagged: "Access, not symptoms, causes the gap" (Module 1), "Symptoms are not the reason; language causes the gap", and the Module 5 / Exercise B notes using "not … cause … proves …" or "caused".
    - **Not flagged:** "It is not surprising that access causes the gap" and "We do not doubt that language barriers cause the gap".
  - Disclaimers that should pass:
    - Correctly passed: "This does not mean that attention causes the gap", "The decomposition cannot tell us whether access causes the gap", and two Module 5 disclaimers.
    - **Wrongly flagged:** "It does not show that symptoms, rather than access, cause the gap", "Nothing here shows what causes the gap", and "We cannot conclude from an accounting exercise that measured symptoms cause the gap".
- **RT2-005.** The round-2 Exercise B text (no gap, no interval, mentions "special health care needs") now gets ✖ on interval and on "compatible with no gap" and ✔ on robustness (it names DFL). It also gets ✖ on "caused".
- **RT-012.** Re-running `quizpos.js` (same hash as `app.js`) shows the correct option is longest in 6 of 25 items. All rewritten option texts were read against the feedback and the outputs. No correct option became wrong and no distractor became right. The exb-3 claim that navigation "collapses in both groups" holds: 63.68 → 22.29 and 66.46 → 31.87.
- **RT2-004.** The p. 38 quotation ("Two stratum identifiers should be used to estimate variance: FIPSSTO … and STRATUM …") was checked against the `pdftotext` output of the Methodology Report and is verbatim. The Wave-1 `FIPSST` = `FIPSSTO` claim matches the round-2 count (21,768 of 21,768).
- **RT2-006 / 007 / 008.** These were checked by reading the R program (sink to `exercise_b_run_log_R.txt`, new cross-checks), the re-run log (run 3) and the README and `pipeline/README.md` text, which agrees with the round-2 pipeline re-run.

## 5. Lab sweep (headless Chromium, `pw.js`)

All 9 pages at 1280 px and 375 px, with every option of all 25 quizzes clicked (94 per width) and every writing task opened:
- 0 console errors or warnings.
- 0 non-file network requests.
- 0 placeholder strings (`undefined`, `NaN`, `{{`, `n/a`, `[missing`, `[exA.`, `[exB.`).
- 0 empty number fields.
- 0 px horizontal overflow.

Keyboard-only use and localStorage-blocked behaviour were not re-tested, because round 3 did not touch that code.

## 6. Not verified

- The Exercise B Python program and the Exercise A programs were not re-run: their sources and outputs are unchanged since round 2, where they were reproduced byte for byte.
- The original program's remaining Section F sensitivities with 200 replicates (only the points in the shipped log were compared).
- A clean install from the lockfiles.

## 7. Statement

Every command above was run by the assessor in this clone. The brief's §5.2 decomposition now reproduces exactly in the repository's own program, and the documentation describes the method correctly. The remaining defect is in the writing checker (RT2-003), plus a minor provenance gap (RT3-001). **Not signed off.**
