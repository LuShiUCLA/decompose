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
