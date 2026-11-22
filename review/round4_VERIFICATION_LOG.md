# Red-team round 4: verification log (HEAD e530b27)

The clone is `.../scratchpad/redteam4/clone`. Nothing under `data/` was changed and nothing was downloaded. Assessor scripts live outside the clone, in `.../scratchpad/redteam4/`.

## 1. What changed
`git diff --stat 052d444 e530b27` lists 8 files:
- README.md
- original_program_sections_EF_run.log
- make_reconciliation.py
- reconciliation.md
- 08-source.html
- lab/source.html
- app.js
- decomposition_lab_core.py

Neither `quizzes.js` nor `05-defence.html` changed.

## 2. RT2-003: browser test of the writing checker
Test script: `pw_check4.js`, run with Playwright and headless Chromium against the built pages.

**What changed:** the new `checklist()` splits the text into sentences on `(?<=[.!?;])\s+`. It quotes every sentence that contains a `none` keyword, escaped with `esc()`, and marks the line "?". The negation regex is gone.

| Text (Module 1 texts are prefixed with the counterfactual sentence; Module 5 and Exercise B texts are padded past 60 words) | Task | Line | Quoted |
|---|---|---|---|
| Access, not symptoms, causes the gap. | M1 | ? | yes |
| It is not surprising that access causes the gap. *(round-3 bypass)* | M1 | ? | yes |
| We do not doubt that language barriers cause the gap. *(round-3 bypass)* | M1 | ? | yes |
| Symptoms are not the reason; language causes the gap. | M1 | ? | "language causes the gap." |
| Attention symptoms, not language, cause the gap, which proves … | M5 | ? | yes |
| It is not a coincidence: symptom differences caused the gap. | M5 | ? | yes |
| Language barriers, not composition, caused the remaining difference … | ExB | ? | yes |
| This does not mean that attention causes the gap. | M1 | ? | yes |
| The decomposition cannot tell us whether access causes the gap. | M1 | ? | yes |
| It does not show that symptoms, rather than access, cause the gap. *(round-3 false positive)* | M1 | ? | yes |
| Nothing here shows what causes the gap. *(round-3 false positive)* | M1 | ? | yes |
| We cannot conclude … that measured symptoms cause the gap. *(round-3 false positive)* | M1 | ? | yes |
| Explained is compositional; this does not prove anything about causes. | M5 | ? | "this does not prove anything about causes." |
| Explained is compositional, and the analysis is not proof of under-diagnosis. | M5 | ? | yes |
| Access causes the gap. This does not mean symptoms cause it. | M1 | ? | both sentences quoted (from `pw_model.js`) |
| …accounting of composition, not a statement about mechanisms. | M1 | ✔ | none |
| Explained is compositional and descriptive. | M5 | ✔ | none |
| The remaining difference is imprecise and compatible with zero. | ExB | ✔ | none |
| Access causes the gap `<img src=x onerror=…>`. | M1 | ? | quoted as text; no `<img>` in the DOM; handler did not run |
| access causes the gap *(no final punctuation)* | M1 | ? | yes |

Other results:
- No ✔ appeared on any line whose text held a listed keyword.
- There were no page errors and no console errors.
- The progress flag is still set after a check, because the code path is unchanged.

**Verdict:** RT2-003 is closed as specified.

### Coverage gaps (RT4-001)
Script: `pw_check5.js`. Each of these gets ✔ on "Avoids causal…":

| Text | Task | Result |
|---|---|---|
| "Attention symptoms cause the gap." | M5 | the whole box is green, all 8 lines ✔ |
| "Language barriers cause the preventive-visit gap." | ExA | ✔ |
| "Language barriers cause the remaining difference." | ExB | ✔ |
| "Language barriers drive the gap." | M1 | ✔ |
| "Language barriers drive the gap." | M5 | ✔ |
| "Symptom differences lead to the gap." | M5 | ✔ |

The keyword lists are in `quizzes.js` at lines 159, 164, 169 and 177.

### Model answers pasted into their own checkers
Script: `pw_model.js`.

| Task | Result |
|---|---|
| Module 1 | all ✔ |
| Module 5 | "?" on "…does not identify causes."; ✖ "Names a sensitivity analysis" (RT4-002); red box (RT4-003) |
| Exercise A | "?" on "…does not identify causes."; red box |
| Exercise B | all ✔ |

## 3. RT3-001: the regenerated section E/F log
- **Header:** lines 1–3 give the date, "200 bootstrap replicates, the program's default", and the full command (`python3 -I … --skip-download --sections E,F`). Every section reports `bootstrap replicates kept: 200/200`.
- **Independent rerun:**
  - I ran the same command with the shipped original program, with `--data-dir` set to my round-2 data folder (a symlink to the same PUF) and `--out-dir` set to scratch.
  - I replaced my out-dir path with `<scratch>/out`, then compared the result with log lines 4–173: `diff` exit 0, so the two are byte-identical.
  - My round-2 run (`redteam2/work/orig/run.log`) matches lines 4–87 exactly:
    - Section E: gap 10.896732, explained 5.015404 (1.713422, 8.317386), n 21,204.
    - Section F primary: n 11,928, gap 8.781804, explained 7.002391 (1.416819, 12.587963).
  - The program's own check reports 17/17 PASS.
- **Where 18,042 comes from:** log line 87 reads `=== sensA_allages_psconly: complete-case n=18,042 (input n=21,481) ===`. Lines 99–100 give gap 9.636290 and explained 5.667445.
  - In the program source (line 1874), sensA is ages 4–23, with the blocks demographics, global, other-PSC and access, and no concrete block. That matches "all-ages sensitivity (PSC only)".
- **Prose checks:**
  - Reconciliation row: n=18,042, gap 9.64, explained 5.67. Correct.
  - README line 47: "gap 9.64". Correct.
  - Sources page, rendered: "on 21,204 children; the brief's n of 18,042 belongs to a different run of that program". The numbers are correct; the "run" wording is the RT4-004 nit.
  - No stale "was not found" or "rather than the 18,042" text remains anywhere in the repository (grep).
- **Docstring:** in the original program, `oaxaca_blinder` is defined at line 1113 and called at line 1777, inside `section_e_tier2_oaxaca` (defined at 1751), and at line 1901, inside `section_f_nathan_synthesis` (defined at 1788). The docstring is accurate.

## 4. Re-runs and the git-diff check
| Step | Result |
|---|---|
| `python3 programs/core/decomposition_lab_core.py` | exit 0; SELF-CHECK 139 PASS, 0 FAIL |
| brief_method | n 13,103; gap 9.67 (5.55, 13.78); explained 8.91 (4.56, 13.25); unexplained 0.76 (−3.55, 5.07), all within ±0.005 of the brief |
| `programs/build_lab_data.py` | ran |
| `lab/_src/build_site.py` | ran |
| `data-notes/make_reconciliation.py` | ran |
| `git status --short` after all of the above | empty, so every regenerated output is byte-identical to the commit |

I did not re-run the R programs this round, because no R file changed between 052d444 and e530b27.

## 5. Page and quiz sweep
Script: `pw.js`, at 1280 px and 375 px, on all 9 pages.
- Quizzes: 25, and every option was clicked: 8 + 12 + 12 + 16 + 21 + 25 = 94 clicks per width.
- Zero console errors, zero network requests, zero placeholder strings, zero empty `data-num` or `data-ci` elements, zero horizontal overflow.
- Every internal link resolves.
