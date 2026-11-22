# Exercise B: population and outcome definitions

All codes below are from the Census `.do` files shipped with each annual file; the year-by-year labels are in `exercise_b_harmonisation.md`.

## Population

| Step | Rule | Note |
|---|---|---|
| CSHCN | `SC_CSHCN = 1` | Census-derived special-health-care-needs status. |
| Publicly insured | `INSTYPE` in (1 public only, 3 private and public) | "Public" is government assistance (Medicaid, CHIP or another government plan). The public-use file does not separate Medicaid from other public plans, so the lab says "publicly insured", not "Medicaid-enrolled". |
| Coordination need | `K5Q20_R = 1` or `K5Q21 = 1` | Someone helped coordinate care, or the caregiver could have used extra help. `K5Q20_R = 3` (did not see more than one provider) is not a need. |
| Household language | `HHLANGUAGE` 1 English; 2 Spanish and 3 Other combined as "other-language" | |

## Outcome: effective navigation (1) vs unmet need (0)

| Value | Rule |
|---|---|
| 1, need met | `K5Q21 = 2` (did not need extra help), or `K5Q21 = 1` and `K5Q22 = 1` (usually got as much help as wanted) |
| 0, unmet need | `K5Q21 = 1` and `K5Q22` = 2 (sometimes) or 3 (never) |
| missing | `K5Q21` missing, or `K5Q21 = 1` with `K5Q22` missing |

`K5Q22` is asked only when `K5Q21 = 1` (in the NSCH-LC Variable List its Universe reads "Skip if K5Q21 in (2, .L)"). A skip because no extra help was needed is information, not missingness: the same logic as Trap 1. The program's "skip trap" run treats it as missing and shows the damage.

This is the builder's operational definition from the questionnaire routing. The design brief mentioned a "CAHMI algorithm" for this outcome; the builder did not have that algorithm's documentation and did not reproduce it. The brief's figures for that analysis (an analytic sample of 26,021, risks of 7.6% vs 26.4%, risk difference −18.8 pp, risk ratio 0.29, E-value 6.44) appear to describe a different comparison (outcomes by navigation status rather than by language; this could not be confirmed) and are **not reproduced or used** in this lab.

## Pooled design

Following the Census *Guide to Multi-Year Estimates* (October 2025): weight `FWC` divided by the number of years (10); strata `FIPSST` × `STRATUM` with "2A" recoded to "2" (102 strata); PSU `HHID` (HHIDs begin with the survey year, so they are unique across years). Only the enhanced ("e") files are used, as the guide instructs.

## Weight revision

The 2016–2021 files were re-released with revised weighting and imputation (2021 in October 2023; 2016–2020 in April 2024, per *NSCH Weighting and Imputation Enhancements*, 25 April 2024), and the multi-year guide says to use only the enhanced ("e") files. For 2016, 2017 and 2018, Census still posts the un-suffixed files (`nsch_<year>_topical.dta`) next to the enhanced ones. Comparing them shows they are the original release: every child's `FWC` differs from the enhanced file, and they still contain race code 6 ("some other race"), which the revision imputed away. The program re-runs the 2016–2018 decomposition with those original weights (everything else from the enhanced files) and compares. No original files are posted for 2019–2021, so the check covers 2016–2018 only; the period split (2016–2021 vs 2022–2025) and leave-one-year-out cover the rest.
