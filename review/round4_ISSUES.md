# Red-team round 4: issues (HEAD e530b27)

Assessor: independent red team. Nothing in the repository was changed; only this file and VERIFICATION_LOG.md were written.

## Status of items open after round 3

| ID | Round-3 severity | Round-4 status | Evidence (details in VERIFICATION_LOG.md) |
|---|---|---|---|
| RT2-003 | major | **Closed** (negation logic) | The checker no longer passes or fails sentences that contain a flagged word. It quotes each one with "?". All 14 round-3 sentences were rerun in Chromium. The 7 causal sentences and the 7 disclaimers were all quoted with "?", and none got a ✔. The two round-3 bypasses ("not surprising", "do not doubt") are now quoted. The three round-3 false positives are now quoted for review rather than marked ✖. A text with two flagged sentences has both quoted. Clean texts get ✔. HTML in a quoted sentence is escaped. There were no console errors. A gap in keyword coverage remains: see RT4-001. |
| RT3-001 | minor | **Closed** | The log header records the command and 200 replicates, and every section shows "replicates kept: 200/200". I ran the same command from scratch with the shipped original program. My output is byte-identical to log lines 4–173 (`diff` exit 0). Lines 4–87 also match my round-2 run. Line 87 reads sensA_allages_psconly n=18,042; gap 9.636290 and explained 5.667445 are at lines 99–100. The reconciliation row, README and Sources page quote these correctly. The docstring is also correct: `oaxaca_blinder` is defined at line 1113 of the original program and called at line 1777 (section E) and line 1901 (section F). |

## New issues

### RT4-001 (major): the writing checker gives a full ✔ to "X cause the gap" on three of four tasks
- **Where:** `lab/assets/quizzes.js`.
  - Line 177 (Module 5 results) flags `caused`, `causes`, `due to`, `proves`, `proof`, …
  - Line 159 (Exercise A) and line 164 (Exercise B) use similar lists.
  - None of the three lists contains the bare plural verb "cause", or "drive" / "lead to".
  - Only Module 1's list (line 169) has `" cause"`.
- **What I saw in Chromium:**
  - Module 5: "Attention symptoms cause the gap." plus filler gets ✔ "Avoids causal and over-claiming verbs" and a green box with every line ✔.
  - Exercise A: "Language barriers cause the preventive-visit gap." gets ✔ "Avoids causal verbs".
  - Exercise B: "Language barriers cause the remaining difference." gets ✔ "Avoids causal and over-claiming verbs".
  - Module 1 and Module 5: "Language barriers drive the gap." gets ✔. Module 1 lists `drives` but not `drive`.
  - Module 5: "Symptom differences lead to the gap." gets ✔.
- **Why it matters:**
  - The builder describes the round-4 design as "only a text with no flagged words gets ✔".
  - That holds, but the flagged-word lists miss the most common causal form, "[plural subject] cause the gap".
  - So the plainest causal claim the lab teaches against still earns a green ✔ on the capstone task.
  - This is the failure RT2-003 was opened for (a ✔ on causal wording), reached through vocabulary rather than negation.
- **Not caused by the round-4 change:** the lists have not changed since 052d444. My round-3 test sentences for these pages all contained "caused" or "proves", so I did not catch it then.

### RT4-002 (minor): the Module 5 model answer fails its own checklist
- **Where:**
  - The model answer is in `lab/_src/pages/05-defence.html` line 82.
  - The rule is in `quizzes.js` line 178. "Names a sensitivity analysis" looks for `sensitivity`, `same-case`, `without the preventive`, `total score` or `reference`.
- **Problem:** the model answer says "Removing the preventive visit from the same sample left the explained part at 8.17 pp". None of the keywords match.
- **Result:** I pasted the model answer into the checker in Chromium and got ✖ "Names a sensitivity analysis — Mention one sensitivity result…". A learner who copies the model's wording is told they left it out.
- **Not caused by the round-4 change:** both files are unchanged since 052d444.

### RT4-003 (minor): a review-only "?" turns the whole feedback box red, including for the lab's own model answers
- **Where:** `app.js` `wireWriting`, `allok = res.every(r => r.ok)`. A "?" line has `ok: false`, so the box gets class `feedback bad`.
- **Effect:**
  - A text whose only flagged sentence is a correct disclaimer is shown in the failure style. Example: "This does not mean that attention causes the gap."
  - The model answers for Module 5 ("…does not identify causes.") and Exercise A ("…does not identify causes.") each get a "?" line and a red box when pasted into their own checker.
  - The "?" text itself says a disclaimer "is fine". The red styling contradicts it.
- **New in round 4:** this is a side effect of the round-4 change.

### RT4-004 (nit): "two runs" / "a different run" describes one execution
- **Where:**
  - The reconciliation row says "reproduces, but **mixes two runs**" and "the n of a different run (section F's all-ages sensitivity)".
  - README line 47 and the Sources page say "belongs to a different run of that program".
- **Problem:** section E and section F's `sensA_allages_psconly` come from the same execution, recorded in the same log, `original_program_sections_EF_run.log`. They are different specifications, not different runs. A reader may look for a second log that does not exist.
- **Accurate wording would be:** "a different specification in the same run (section F's all-ages sensitivity)". The numbers quoted are correct.

## Counts
- Round-3 items: 2 verified. 2 closed (RT2-003, RT3-001), 0 still open.
- New: 4. Severity: 1 major (RT4-001), 2 minor (RT4-002, RT4-003), 1 nit (RT4-004). Only RT4-003 comes from the round-4 change; RT4-001 and RT4-002 predate it but were found this round.
- Sign-off: **not yet**, because of RT4-001.
