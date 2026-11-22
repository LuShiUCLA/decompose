# Red-team round 5: verification log (HEAD 46d1d67)

The clone is `.../scratchpad/redteam5/clone`. Nothing under `data/` was changed and nothing was downloaded. Assessor scripts are in `.../scratchpad/redteam5/`, outside the clone.

## 1. What changed
`git diff --stat e530b27 46d1d67` lists 7 files: README.md, make_reconciliation.py, reconciliation.md, 08-source.html, lab/source.html, app.js and quizzes.js.

| File | Change |
|---|---|
| `quizzes.js` | Adds one shared `CAUSAL` list (24 phrases), used by all four tasks. Exercise B adds "no disparity" and "no difference exists"; Module 5 results adds "no under-diagnosis", "no underdiagnosis", "rules out" and "rule out". The Module 5 sensitivity keywords add "same sample", "same children", "removing the preventive" and "preventive visit removed". |
| `app.js`, `checklist()` | Each keyword is regex-escaped and matched as a whole word, between non-letters or the string edges. |
| `app.js`, `wireWriting` | `allok` now counts a review item as passing. |

## 2. Writing checker in headless Chromium (Playwright)

### Round-4 regression set (`pw_check4.js`, 20 texts)
- All 20 results are as expected.
- The 15 texts with flagged words each get "?" and their sentences are quoted. Both sentences of the two-sentence text are quoted.
- The 3 clean texts get ✔.
- HTML injection is escaped and does not run.
- Text without final punctuation is still caught.
- Box colour:
  - Green when the only non-✔ line is a "?".
  - Red only for the Exercise B texts, where "Reports a robustness check" is ✖, which is correct.
- There were no console errors or page errors.

### RT4-001 sentences and new forms (`pw_check5.js`)
| Text | Task | Result |
|---|---|---|
| Attention symptoms cause the gap. | M5 | ? quoted, green |
| Language barriers cause the preventive-visit gap. | ExA | ? quoted |
| Language barriers cause the remaining difference. | ExB | ? quoted |
| Language barriers drive the gap. | M1 | ? quoted |
| Language barriers drive the gap. | M5 | ? quoted |
| Symptom differences lead to the gap. | M5 | ? quoted |
| Access differences result in the gap. | ExA | ? quoted |
| Language is responsible for the difference. | ExB | ? quoted |
| The gap is driven by access. | M1 | ? quoted |
| Causing the gap, access matters most. | M1 | ? quoted |
| Interpreter services would eliminate the gap. | M5 | ? quoted |
| The analysis rules out under-diagnosis. | M5 | ? quoted |
| Access is the cause of the gap. | M1 | ? quoted |
| Because the groups differ in composition, part of the gap is accounted for. | M1 | ✔ (whole word: "because" is not "cause") |
| The causal question is outside this design; explained is compositional. | M5 | ✔ |
| **Language barriers drove the gap.** | M1 | **✔ (RT5-001)** |
| **This proved that access matters.** | M1 | **✔ (RT5-001)** |
| **These results prove that access matters. It is proven that access matters.** | M1 | **✔ (RT5-001, from `pw_model2.js`)** |
| Symptoms explain why the gap exists. | M1 | ✔ (outside the stated list; not counted) |

### Model answers pasted into their own checkers (`pw_model2.js`)
Each model answer is the `.model` text from the built page.

| Task | Result | Box |
|---|---|---|
| Module 1 counterfactual | all 4 ✔ | green |
| Module 5 results | 7 ✔ and 1 "?" (the disclaimer "…does not identify causes."). "Names a sensitivity analysis" is now ✔ (RT4-002 closed). | green (RT4-003 closed) |
| Exercise A | 4 ✔ and 1 "?" (the disclaimer) | green |
| Exercise B | all 4 ✔ | green |

## 3. Wording (RT4-004)
- `reconciliation.md` row: "reproduces, but **mixes two specifications**"; "…the n of a different specification in the same run (section F's all-ages sensitivity)". The numbers are unchanged: n=18,042, gap 9.64, explained 5.67, the same as round 4, which I verified against my own rerun.
- README line 47: "belongs to a different specification in the same run (an all-ages sensitivity with gap 9.64)".
- Sources page as rendered: "…belongs to a different specification in the same run of that program."
- I grepped for "different run" and "two runs": the only hit is README line 60, which is about the reviewed pipeline's 17 and 22 November runs. Those are genuinely two runs, so it is correct.

## 4. Re-runs and the git-diff check
| Step | Result |
|---|---|
| `python3 programs/core/decomposition_lab_core.py` | exit 0; SELF-CHECK 139 PASS, 0 FAIL |
| brief_method | n 13,103; gap 9.67 (5.55, 13.78); explained 8.91 (4.56, 13.25); unexplained 0.76 (−3.55, 5.07) |
| `programs/build_lab_data.py` | exit 0 |
| `lab/_src/build_site.py` | exit 0 |
| `data-notes/make_reconciliation.py` | exit 0 |
| `git status --short` after all of the above | empty before this file and ISSUES.md were written, so every regenerated output is byte-identical to the commit |

I did not re-run the R programs, because no R or analysis file changed.

## 5. Page and quiz sweep
Script: `pw.js`, at 1280 px and 375 px, on all 9 pages.
- Quizzes: 25 per width, 50 in all, with every option clicked: 94 clicks per width, 188 in all.
- Zero console errors, zero network requests, zero placeholder strings, zero empty `data-num` or `data-ci` elements, zero horizontal overflow.
- 0 missing internal link targets.
