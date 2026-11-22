# Data notes

## Files and checksums (SHA-256)

| File | Source URL | SHA-256 |
|---|---|---|
| `nschlc_2024_puf_Stata.zip` | https://www2.census.gov/programs-surveys/nsch-lc/datasets/2024/nschlc_2024_puf_Stata.zip | `02200328bf93abf484f2ba21413265268dd27363e6686d3760fe0caffa67308d` |
| `nschlc_2024_puf.dta` (extracted) | same zip | `d483c989262b2ce4a36173b2e7fd63d2a3edfddaa1b7ef2372ff8abcd99799ce` |
| `NSCH-LC-Variable-List.xlsx` (copy in `sources/`) | https://www2.census.gov/programs-surveys/nsch-lc/technical-documentation/2024/NSCH-LC-Variable-List.xlsx | `1bd036cc2eb45f5841844cc4c0c7447e68a0d91c7abc4f6f36fd8999e3429ae7` |
| Methodology Report, Source and Accuracy Statement, FAQs, imputed-data guide, 2024 questionnaire | URLs and checksums in `sources/documentation_manifest.json` | |

**Download log.** All of these were downloaded from census.gov on 17 November 2026 by the project's earlier work (the research brief and conference abstract on the same study) and are kept in the project's shared folder `Society of Behavioral Medicine/data/` and `.../evidence/`. They were not downloaded again for this lab; the `.dta` used here was copied from that folder and its checksum matches the one recorded in the earlier pipeline's `run_manifest.json` (copy in `logged_reference/`). The programs re-download the zip from the URL above if `data/` is empty; the Python programs print a warning if the `.dta` checksum differs from the reference run's (Census may re-release files).

## What else is here

| File | What it is |
|---|---|
| `codebook_excerpts.md` | The Variable List rows the lab relies on, copied verbatim by `extract_codebook.py`. Note the 2024 column: K5Q20_R, K5Q21, K5Q22 and K4Q27 are **N** (not on the 2024 follow-up file), which is why Exercise B uses the annual NSCH. |
| `logged_reference/` | Verbatim copies of the earlier pipeline's logged output tables (run 17 November 2026; re-run 22 November 2026 with identical results). |
| `make_reference_values.py` → `reference_values.json` | The reference values the programs' self-checks use. Generated from `logged_reference/`; no number is typed by hand. |
| `census_excerpts.md` | Verbatim passages from the Methodology Report and the Source and Accuracy Statement that the lab cites (telephone languages, weights, strata and PSU), with the PDFs' checksums. |
| `brief_values.json` | The design brief's figures, copied only so the core programs can test whether they reproduce. |
| `make_reconciliation.py` → `reconciliation.md` | Every figure quoted in the lab's design brief, against the reproduced value, with status. |
| `exercise_a_covariates.md` | Why Exercise A uses the covariates it uses. |

## Key design facts (Source and Accuracy Statement, PDF p. 6; quoted in `census_excerpts.md`)

- Weight `FWC`; strata `FIPSSTO` × `STRATUM` with stratum "2A" recoded to "2" (102 strata); PSU `HHID` (one child per household).
- Variance: Taylor series with replacement; domain estimation on the full design (no pre-subsetting).
- Family income relative to poverty is multiply imputed (`FPL_I1`–`FPL_I6`); analyses are run six times and combined with Rubin's rules (Census guide to multiply imputed data).

## Coding decisions

- **Trap 1.** K4Q20R's Universe is "Skip if S4Q01 = 2". Those children had no health care visit, so their preventive-visit indicator is a structural 0. A K4Q20R answer is used whenever one exists. Among children aged 6–17, 49 stay missing: 37 with a visit but no K4Q20R answer, and 12 with S4Q01 missing and no K4Q20R answer (one more S4Q01-missing child answered K4Q20R).
- **Trap 2.** CURRCOV's description says "(Use CURRINS)". The lab uses CURRINS.
- **Language group.** `HHLANGUAGE` at baseline (2018/2019): 1 English, 2 Spanish, 3 Other; 2 and 3 are combined as "other-language" for the decomposition.
- **Attention items.** The five PSC-17 attention items (coded 1 = Never, 2 = Sometimes, 3 = Often) are shifted to 0–2 (Never 0, Sometimes 1, Often 2), the scoring the Variable List gives for `PSCATT`, so a coefficient reads "per step"; `PSCATT` is the Census-released 0–10 attention score, which counts an unanswered item as 0 (Variable List). Summing the five items only for children who answered all five (the design brief's scoring) gives means of 2.398 vs 1.535; `PSCATT` gives 2.403 vs 1.497. The lab's descriptives and the total-score sensitivity rows use `PSCATT`; the primary decomposition uses the items themselves.
- **Caregiver mental health.** Poor (fair or poor, codes 4–5) if any caregiver reports it; not poor only if every present caregiver answered 1–3 (`A2_RELATION` = 8 means there is no second caregiver). The project's earlier rule, which reproduces the design brief's figures, also coded 'not poor' when a present second caregiver had not answered; it is kept as `CAREGIVER_POOR_MH_EARLIER_RULE` for the Module 5 sensitivity row.
