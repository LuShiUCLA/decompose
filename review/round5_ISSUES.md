# Red-team round 5: issues (HEAD 46d1d67)

Assessor: independent red team. Nothing in the repository was changed; only this file and VERIFICATION_LOG.md were written. The scope is the round-4 findings and anything the round-5 changes could break.

## Status of the round-4 findings

| ID | Round-4 severity | Round-5 status | Evidence (details in VERIFICATION_LOG.md) |
|---|---|---|---|
| RT4-001 | major | **Closed** | Every round-4 sentence is now quoted with "?", and none gets ✔. That covers "Attention symptoms cause the gap." (Module 5), "Language barriers cause …" (Exercises A and B), "drive the gap" (Module 1 and Module 5) and "lead to the gap". New forms are caught too: "result in", "responsible for", "driven by", "Causing …", "would eliminate", "rules out", "the cause of". Whole-word matching does not catch "Because …" or "The causal question …" (both get ✔). All 20 round-4 regression texts behave as before. |
| RT4-002 | minor | **Closed** | The Module 5 model answer pasted into its own checker now gets ✔ "Names a sensitivity analysis". |
| RT4-003 | minor | **Closed** | A "?" no longer turns the box red. The model answers for Module 5 and Exercise A now show a green box with a "?" line. The box is still red when a required item is ✖, for example Exercise B text without a robustness check. |
| RT4-004 | nit | **Closed** | The reconciliation, README line 47 and the Sources page (built from source and checked as rendered) now say "a different specification in the same run" and "mixes two specifications". No "different run" wording remains. The "two runs" on README line 60 is about a different pair of runs, which really are two runs. |

## New issue

### RT5-001 (minor): the shared CAUSAL list misses some inflections of verbs it already covers
- **What is missing:** `quizzes.js` lists drive, drives, driven by and driving, but not "drove". It lists proves and proof, but not "prove", "proved" or "proven".
- **Effect in Chromium:** these Module 1 texts all get ✔ "Avoids causal language" and a green box:
  - "Language barriers drove the gap."
  - "This proved that access matters."
  - "These results prove that access matters. It is proven that access matters."
  - The same list serves all four tasks, so the others behave the same way.
- **Suggested fix:** add "drove", "prove", "proved" and "proven".
- **Out of scope:** "explain why" is also not flagged, but that is beyond the stated list, so I don't count it as a defect.

## Counts
- Round-4 items: 4 checked. 4 closed (RT4-001, RT4-002, RT4-003, RT4-004), 0 still open.
- New: 1 minor (RT5-001). No blocker, major or nit.
- Sign-off: **yes**, with RT5-001 recommended as a small follow-up. It is a gap in keyword coverage within a heuristic the page itself labels "keyword-based, so read each line critically", and every major item is closed.
