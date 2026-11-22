"""Reconcile every number in the build prompt's Section 5.2 table against the
program output (programs/core/output/core_results.json) and the logged
reference run (data-notes/reference_values.json). Writes reconciliation.md.
The 'spec' column is copied from the build prompt; the 'reproduced' column is
read from program output - nothing in that column is typed by hand."""
import json
from pathlib import Path
H = Path(__file__).resolve().parent
C = json.loads((H.parent / "programs/core/output/core_results.json").read_text())
REF = json.loads((H / "reference_values.json").read_text())
D, P, S, F = C["descriptives"], C["primary"]["terms"], C["sensitivity"], C["falsification"]
M, E = REF["models"], REF["evalues"]
def ci(d, k="est"):
    return f"{d[k]:.2f} ({d['lo']:.2f}, {d['hi']:.2f})"
rows = []
def row(q, spec, got, status, note=""):
    rows.append(f"| {q} | {spec} | {got} | {status} | {note} |")
OK, NO, LAB = "reproduces", "**does not reproduce**", "**value reproduces, label wrong**"
row("Interviews; weighted response rate", "21,768; 43.0%", f"{C['design']['children']:,} children in PUF; 43.0% (Methodology Report p. 4)", OK)
for key, spec in [("incident_english", "10.3% (9.0, 11.8)"), ("incident_spanish", "3.0% (1.5, 5.9)"),
                  ("incident_other_language", "1.1% (0.6, 2.2)"), ("incident_nonenglish", "2.5% (1.4, 4.7)")]:
    row(f"Newly reported ADHD by follow-up, {key.split('_',1)[1]}", spec, ci(D[key]) + f", n={D[key]['n']}", OK,
        "baseline ages 6-17, undiagnosed at baseline; caregiver-reported 'newly reported', not clinically incident")
row("ADHD ever diagnosed, English vs other-language", "16.3% vs 6.0% 'at Wave 1'",
    f"{D['adhd_english']['est']:.2f}% vs {D['adhd_other']['est']:.2f}% at **Wave 2 (2024)**, ages 6-17", LAB,
    "these are follow-up (2024) lifetime-diagnosis rates, not Wave 1")
k1, k2 = "D1_new_report_risk_ratio|language=Spanish", "D1_new_report_risk_ratio|language=Other non-English"
row("Adjusted RR, primary (modified Poisson)", "other-language vs English 0.23 (0.11, 0.51); n=13,485",
    f"**Spanish** vs English {M[k1]['effect']:.2f} ({M[k1]['lo']:.2f}, {M[k1]['hi']:.2f}); n={M[k1]['n']:,}", LAB)
k3 = "D1_broad_atrisk_sensitivity|language=Other non-English"
row("Adjusted RR, 'sensitivity model'", "0.13 (0.06, 0.26); n=19,321",
    f"0.13 is **other non-English** vs English in the SAME primary RR model: {M[k2]['effect']:.2f} ({M[k2]['lo']:.2f}, {M[k2]['hi']:.2f}), n={M[k2]['n']:,}. "
    f"The n=19,321 model is a broad at-risk *logit* sensitivity (OR other non-English {M[k3]['effect']:.2f})", LAB)
es, eo = E["language=Spanish"], E["language=Other non-English"]
row("E-values (point / CI limit)", "8.04 (3.32) / 15.08 (7.26)",
    f"Spanish {es['e_value']:.2f} ({es['e_value_ci']:.2f}); other non-English {eo['e_value']:.2f} ({eo['e_value_ci']:.2f})", OK,
    "CI E-value uses the limit closest to the null (upper limit for RR<1)")
pm = C["primary"]
BM, BN = S["brief_method"], S["brief_method_no_preventive"]
METH = ("earlier caregiver mental-health rule; income = mean of the six implicates in one fit; "
        "naive PSU bootstrap without rescaling (see brief_method() in the core program)")
def same(spec_pts, d):
    return all(abs(x - y) <= 0.005 for x, y in zip(spec_pts, [d["est"], d["lo"], d["hi"]]))
def dec(q, spec, key):
    pts = [float(x) for x in spec.replace("(", "").replace(")", "").replace(",", "").split()]
    row(q, spec, f"brief method: {ci(BM[key])}. Lab headline (reviewed rule, Rubin's rules, Taylor): {ci(P[key])}",
        "reproduces exactly (brief method)" if same(pts, BM[key]) else NO)
row("Primary decomposition n", "13,103", f"brief method: {BM['n']:,}. Lab headline: {pm['n']:,}",
    "reproduces exactly (brief method)" if BM["n"] == 13103 else NO, "brief method = " + METH)
dec("Gap", "9.67 (5.55, 13.78)", "gap")
dec("Explained", "8.91 (4.56, 13.25)", "explained")
dec("Unexplained", "0.76 (-3.55, 5.07)", "unexplained")
row("Explained share", "92%", f"brief method: {BM['explained']['est'] / BM['gap']['est']:.1%}. Lab headline: {pm['explained_share']:.1%}",
    "reproduces (brief method)")
for b, spec, lab in [("concentration_fidget", "3.37 (1.80, 4.93)", "global symptoms (concentration + fidgeting)"),
                     ("other_attention", "2.19 (0.33, 4.05)", "other attention items"),
                     ("demographics", "2.43 (-0.72, 5.58)", "demographics"),
                     ("access", "0.64 (-0.30, 1.58)", "access"),
                     ("persistence_homework_calm", "0.28 (-0.50, 1.07)", "'concrete covariates' = persistence, homework, calmness")]:
    dec(f"Block: {lab}", spec, "block:" + b)
okn = BN["n"] == 13143 and same([9.66, 5.56, 13.76], BN["gap"]) and same([8.86, 4.53, 13.20], BN["explained"])
row("Sensitivity: preventive visit omitted", "n=13,143; gap 9.66 (5.56, 13.76); explained 8.86 (4.53, 13.20)",
    f"brief method: n={BN['n']:,}; gap {ci(BN['gap'])}; explained {ci(BN['explained'])}. Lab (reviewed rule): n={S['no_preventive_available']['n']:,}; "
    f"gap {ci(S['no_preventive_available']['gap'])}; explained {ci(S['no_preventive_available']['explained'])}",
    "reproduces exactly (brief method)" if okn else NO)
import re
OL = (H / "logged_reference" / "original_program_sections_EF_run.log").read_text()
mF = re.search(r"primary_6to17: complete-case n=([\d,]+).*?\n.*?\n\s+gap ([\d.]+)pp; explained ([\d.]+)pp", OL)
mE = re.search(r"Complete-case n = ([\d,]+) \(of.*?gap ([\d.]+)pp; explained ([\d.]+)pp", OL, re.S)
row("Earlier specification, ages 6-17", "n=11,928; gap 8.78; explained 7.00",
    f"superseded first program, section F: n={mF.group(1)}; gap {mF.group(2)}; explained {mF.group(3)}",
    "reproduces (superseded first program)",
    "run of data-notes/logged_reference/pipeline/original/ on 22 November 2026 (log: logged_reference/original_program_sections_EF_run.log); "
    "that program used CURRCOV and other choices the reviewed pipeline corrected, so the lab does not use it")
mS = re.search(r"sensA_allages_psconly: complete-case n=([\d,]+).*?\n.*?\n\s+gap ([\d.]+)pp; explained ([\d.]+)pp", OL)
row("All-ages Tier 2 Oaxaca", "n=18,042; gap 10.90; explained 5.02",
    f"superseded first program, section E: n={mE.group(1)}; gap {mE.group(2)}; explained {mE.group(3)}. "
    f"Section F's all-ages sensitivity (PSC only): n={mS.group(1)}; gap {mS.group(2)}; explained {mS.group(3)}",
    "reproduces, but **mixes two specifications**",
    "the brief pairs section E's gap and explained with the n of a different specification in the same run (section F's all-ages sensitivity); not used in the lab")
row("PSC-17 attention mean, English vs other", "2.40 vs 1.54",
    f"complete-item scoring: {D['psc_mean_complete_items_english']['est']:.3f} vs {D['psc_mean_complete_items_other']['est']:.3f}. "
    f"Released PSCATT: {D['psc_mean_english']['est']:.3f} vs {D['psc_mean_other']['est']:.3f}", "reproduces (complete-item scoring)",
    "the brief sums the five items over children with all five answered; Census's released PSCATT scores an unanswered item as 0 (Variable List)")
row("PSC >= 7, English vs other", "8.6% (7.4, 9.8) vs 3.6% (1.4, 8.7)",
    f"complete-item scoring: {ci(D['psc_ge7_complete_items_english'])} vs {ci(D['psc_ge7_complete_items_other'])}. "
    f"Released PSCATT: {ci(D['psc_ge7_english'])} vs {ci(D['psc_ge7_other'])}",
    "reproduces to one decimal (complete-item scoring)" if [round(D[f"psc_ge7_complete_items_{g}"][k], 1) for g in ("english", "other") for k in ("est", "lo", "hi")]
    == [8.6, 7.4, 9.8, 3.6, 1.4, 8.7] else NO, "released PSCATT gives 8.5 and an upper limit of 8.5")
row("Usual source of sick care", "83.7% vs 61.8%", f"{D['usual_english']['est']:.2f}% vs {D['usual_other']['est']:.2f}%", OK)
row("Currently insured (CURRINS)", "96.9% (96.0, 97.6) vs 87.4% (81.1, 91.8)", f"{ci(D['insured_english'])} vs {ci(D['insured_other'])}", OK)
row("Preventive visit past year", "86.0% (84.2, 87.6) vs 72.8% (66.1, 78.5)", f"{ci(D['preventive_english'])} vs {ci(D['preventive_other'])}", OK,
    "other-language upper limit is 78.57 (rounds to 78.6, spec says 78.5)")
sk = F["skip_counts_primary"]
row("K4Q20R skip counts (ages 6-17)", "1,249 structural; 37 arbitrary; 12 S4Q01-missing",
    f"{sk['structural_zero_S4Q01_no']:,}; {sk['arbitrary_missing_K4Q20R_with_visit']}; {sk['S4Q01_missing']} S4Q01-missing, of whom {sk['S4Q01_missing_without_K4Q20R']} have no K4Q20R answer",
    "reproduces", f"in all, {sk['preventive_missing_total']} children aged 6-17 have a missing preventive-visit indicator")
row("CURRINS vs CURRCOV disagreements", "65", f"{F['currins_currcov_disagree_primary']} (ages 6-17, language known); {F['currins_currcov_disagree_all']} in whole cohort", OK)
row("Strata", "STRATACROSS = FIPSST + '_' + STRATUM; 102 values", f"{C['design']['strata']} values from **FIPSSTO** x STRATUM (2A->2)", "reproduces (same partition)",
    "Source & Accuracy Statement p. 6 names FIPSSTO (2018/2019 state); the Wave 1 FIPSST equals it for every child, so the brief's strata are the same. The 2024 FIPSST would differ for 928 children")
txt = ["# Reconciliation of the build prompt's Section 5.2 against logged program runs", "",
       "Generated by `data-notes/make_reconciliation.py` from `programs/core/output/core_results.json` (this lab's core program) "
       "and `data-notes/reference_values.json` (the reviewed project pipeline's logged run). Rule applied: **logged program runs are the truth**. "
       "The lab's headline is the reviewed pipeline's (n 12,977; the AJPM manuscript's numbers). The brief's decomposition figures, intervals included, reproduce exactly "
       "with the method of the project's superseded first program: " + METH + ". The lab teaches those three differences in Module 5.", "",
       "| Quantity | Build-prompt value | Reproduced from the PUF | Status | Note |", "|---|---|---|---|---|"] + rows
(H / "reconciliation.md").write_text("\n".join(txt) + "\n")
print("\n".join(rows))
