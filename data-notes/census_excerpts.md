# Census documentation passages the lab relies on (verbatim)

U.S. Census Bureau publications are works of the U.S. Government and are not subject to copyright. Passages are copied word for word from text extracted with `pdftotext -layout`; page numbers are PDF page numbers. Source URLs are in `references/references.md`.

| Document | SHA-256 of the PDF used |
|---|---|
| NSCH-LC 2024 Methodology Report | `8dacb1191a12d277527f512bbe5f4b6e16adb03a186caf732dae0e2824c1a8af` |
| NSCH-LC 2024 Source and Accuracy Statement | `7872a140862b080001696590d249c0af435741472e9ebb6d8899fa269926ac47` |

## Telephone assistance languages (Module 1)

Methodology Report, PDF p. 11:

> The NSCH-LC could be completed over the phone with support of trained TQA interviewers certified in the following languages: English, Spanish, Mandarin, Russian, Hindi, and Portuguese.

## Weights (Module 3)

Methodology Report, PDF p. 35:

> FWC is a product of the final child-level weight from the 2018/2019 NSCH, a nonresponse adjustment, and raking to population controls. Population controls are derived from the child population in the 2018 and 2019 American Community Surveys (ACS) as an average between the two years, so estimates from the weighted NSCH-LC derived using FWC represent the child population from which this sample was originally selected.

## Survey design: strata and PSU (Module 3; all programs)

Source and Accuracy Statement, PDF p. 6:

> Standard errors for the NSCH-LC estimates can be obtained using the Taylor Series approximation method, which is available in software packages such as SAS, Stata, and SUDAAN. The sampling strata are identified by state and the child stratum flag, and the Primary Sampling Unit (PSU) is the household.

> strata FIPSSTO STRATUM
> cluster HHID
> weight FWC (final child/young adult LC weight)

> replace stratum = "2" if stratum == "2A"
> destring stratum, replace
> egen stratacross=group(fipssto stratum)

Methodology Report, PDF p. 38, gives the same design in prose:

> Two stratum identifiers should be used to estimate variance: FIPSSTO (state of residence in 2018/2019) and STRATUM (identifies households flagged with children).

and the crossing `EGEN STRATACROSS = GROUP (fipssto stratum)`; it does not repeat the Taylor sentence, the SAS statements or the "2A" recode.

**Why this matters.** The design brief wrote `FIPSST`. In this file the Wave 1 (2018/2019) `FIPSST` equals `FIPSSTO` for all 21,768 children, so the brief's strata and Census's are the same partition. The Wave 2 (2024) `FIPSST` differs from `FIPSSTO` for 928 children; using it would put those children in the wrong strata. The lab names `FIPSSTO`, as Census does (counts computed with `programs/lib/nschlc_prepare.py`, 22 November 2026).
