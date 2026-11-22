# Exercise A: covariate choices

Outcomes (2024 follow-up, children aged 6–17, baseline household language known):
`PREVENTIVE_W2` (K4Q20R with the S4Q01 structural-zero rule) and `USUAL_SOURCE_W2` (K4Q01).

| Block | Variables | Why it is in | Caveat |
|---|---|---|---|
| Demographics | AGE, SEX, RACE4, HISPANIC | Who the child is. | RACE4 collapses SC_RACE_R codes 3, 5 and 7 into one "other or multiple race" category: codes 3 (n = 71 aged 6–17) and 5 (n = 39) are too sparse for a logit refitted in 200 bootstrap replicates. |
| SES | FPL (six implicates), EDUCATION | Family resources. | Income is imputed; Rubin's rules carry the imputation uncertainty. |
| Insurance | INSURED_W2 (CURRINS, Trap 2) | Coverage is the classic access covariate. | Insurance is itself part of access; read "explained by insurance" as "lines up with the insurance difference". |
| Health need | FAIR_POOR_HEALTH_W2 (K2Q01 = 4 or 5), SHCN_W2 (SC_CSHCN = 1) | Children with more need use more care; without need, a gap in use cannot be read. | Caregiver-reported, so reporting may differ by language. |
| Other access | the other outcome | Included in specification A to show the problem. | **Circular**: access explaining access. Specification B drops it. |

Specification C re-introduces both traps (skips dropped, CURRCOV) as a falsification run.
Variable definitions are in `codebook_excerpts.md`.
