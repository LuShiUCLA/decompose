# Issues: independent red-team review

**Status: 0 open.** An independent assessor reviewed the repository in five rounds (22 November 2026), each on a fresh clone. It re-ran every program in both languages, rebuilt the site, checked every displayed number and swept all pages in a browser. The full record of each round is in `review/`.

| Round | HEAD reviewed | Findings | Outcome |
|---|---|---|---|
| 1 | f7553e5 | 23 (1 blocker, 6 major, 16 minor) | all fixed by 6e10413, except RT-012 |
| 2 | 6e10413 | RT-012 still open; 8 new (1 blocker, 2 major, 5 minor) | fixed in 052d444 |
| 3 | 052d444 | RT2-003 still open; 1 new minor | fixed in e530b27 |
| 4 | e530b27 | 4 new (1 major, 2 minor, 1 nit) | fixed in 46d1d67 |
| 5 | 46d1d67 | 1 new minor (RT5-001); **signed off** | RT5-001 fixed in the next commit |

RT5-001 (the causal-word list lacked "drove", "prove", "proved" and "proven"): those four words were added to `CAUSAL` in `lab/assets/quizzes.js`. "Language barriers drove the gap.", "This proved that access matters." and "It is proven." are now quoted for review on all four writing tasks, and every model answer still passes its own checklist. The builder ran this check; the assessor did not re-run it after the sign-off.

## Beginner test of the live site (22 November 2026)

An outside test run, in the role of an MPH student new to decomposition, reported 3 blockers, 6 majors and 5 minors on the live site. Each was handled as follows (builder-fixed and builder-tested in a browser; not re-run by the assessor).

| Finding | Disposition |
|---|---|
| B1 Checkpoint fails the brief's 9.67 / 8.91 / 0.76 | The checkpoint now accepts the brief's figures and the earlier-rule figures as correct reproductions and names which coding they match. The home page shows both sets of numbers side by side, with the reason in plain words. |
| B2 Programs not reachable from the site | Repository and zip links on the home page, the Sources page and every page footer; one-line R run command on the home page (added earlier the same day). |
| B3 Exercise B "does not match the assigned question" | Not changed in substance: the brief's figures (n 26,021; RD −18.8) could not be traced to a by-language comparison and the CAHMI algorithm was unavailable (`data-notes/exercise_b_outcome.md`). The page now says what the exercise answers, that "publicly insured" is not "Medicaid-enrolled", that the outcome is the lab's own definition, why the brief's figures are not used, and why no RR or E-value is shown. |
| M4 Three-choices table unexplained | Plain-language paragraph added; anchor linked from the home page. |
| M5 16.29 − 5.97 ≠ 9.77 | Module 1 now shows both gaps and why they differ (all children vs complete cases). |
| M6 Writing checker false passes | Sample-size and CI checks now require the actual numbers (n, estimate and both limits, read from the lab data, matched with number boundaries). |
| M7 Case C contradictory feedback | Diagnosis and (ungraded) prediction are reported separately; "higher" is acknowledged as strictly true but negligible. |
| M8 102 strata, n differences, period split | Notes added: why ten years give 102 strata and df = PSUs − strata; why the decomposition n is smaller; how to read a sign flip with wide intervals; why Exercise A's n differs from the core's. |
| M9 Review status not on the site | "How this lab was checked" section on the Sources page, including that the final fixes were builder-checked and that the pipeline code is held back until publication. |
| m10 No Exercise A README | Added `programs/exercise-a/README.md`; stale "pooled coefficients" docstring corrected. |
| m11 Sensitivity table without CIs; 126 not computed | Intervals added to every row that has them; 126 computed from the data. |
| m12 Survey page vs data page | Census data page link added (checked: HTTP 200). |
| m13 Fairlie explained > gap | Explained on the Exercises page (negative unexplained part). |
| m14 Undefined jargon | New Glossary page; the first use of each term on each page links to it. |
| Module 2 complete-case means differ from Module 4 | Note added. |
| Blocks sum to 8.20 not 8.19 | Rounding note with the unrounded sum. |
| 21,768 not written | Module 3 now states it in words. The 43.0% response rate is not added: it was not verified against the Census documentation. |
| Ever-diagnosed label and rate-ratio labels | Not changed: the lab's labels follow the 2024 variables and the logged pipeline output (`data-notes/reconciliation.md`). |
