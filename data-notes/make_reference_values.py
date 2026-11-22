"""Build data-notes/reference_values.json from the LOGGED outputs of the
reviewed project pipeline (copied verbatim into data-notes/logged_reference/).
No number in reference_values.json is typed by hand."""
import json
from pathlib import Path
import pandas as pd
H = Path(__file__).resolve().parent
L = H / "logged_reference"
d = pd.read_csv(L / "descriptive_statistics.csv")
x = pd.read_csv(L / "decompositions_mi_pooled.csv")
m = pd.read_csv(L / "models_mi_pooled.csv")
ev = pd.read_csv(L / "evalues_risk_ratio.csv")
def desc(dom, grp, var, scale=100):
    r = d[(d.domain == dom) & (d.group == grp) & (d.variable == var)].iloc[0]
    return dict(est=r["mean"] * scale, lo=r.ci_low * scale, hi=r.ci_high * scale, n=int(r.n))
def dec(spec, term):
    r = x[(x.specification == spec) & (x.term == term)].iloc[0]
    return dict(est=r.coef, lo=r.ci_low, hi=r.ci_high, n=int(r.n))
R = {"source": "Reviewed pipeline nsch_lc_adhd_language_gap.py, logged run (results/*.csv); re-run 2026-11-22 identical to 1e-14",
     "descriptives": {}, "decompositions": {}, "models": {}, "evalues": {}}
P = "primary_age6to17"
for key, var, sc in [("adhd", "ADHD_EVER_W2", 100), ("psc_mean", "PSCATT", 1), ("psc_ge7", "PSC_GE7", 100),
                     ("usual", "USUAL_SOURCE_W2", 100), ("insured", "INSURED_W2", 100), ("preventive", "PREVENTIVE_W2", 100)]:
    R["descriptives"][f"{key}_english"] = desc(P, "English", var, sc)
    R["descriptives"][f"{key}_other"] = desc(P, "Non-English", var, sc)
for key, grp in [("english", "English"), ("spanish", "Spanish"), ("other_language", "Other non-English"), ("nonenglish", "Non-English")]:
    R["descriptives"][f"incident_{key}"] = desc("baseline_age6to17", grp, "NEW_REPORTED_ADHD")
blockmap = {"demographics": "demographics", "concentration_fidget": "concentration_fidget_items",
            "other_attention": "other_attention_items", "persistence_homework_calm": "persistence_homework_calm",
            "access": "access", "psc_total": "PSC_attention"}
for spec in x.specification.unique():
    out = {}
    for t in ["gap", "explained", "unexplained"]:
        out[t] = dec(spec, t)
    for k, v in blockmap.items():
        if ((x.specification == spec) & (x.term == "explained_block:" + v)).any():
            out["block:" + k] = dec(spec, "explained_block:" + v)
    R["decompositions"][spec] = out
for model in ["D1_new_report_risk_ratio", "D1_broad_atrisk_sensitivity", "D1_new_report_baseline_schoolage"]:
    for _, r in m[(m.model == model) & m.term.str.startswith("language=")].iterrows():
        R["models"][f"{model}|{r.term}"] = dict(effect=r.effect, lo=r.effect_low, hi=r.effect_high, n=int(r.n),
                                                 scale=r.effect_scale)
for _, r in ev.iterrows():
    R["evalues"][r.term] = dict(rr=r.adjusted_RR, e_value=r.E_value, e_value_ci=r.E_value_CI)
(H / "reference_values.json").write_text(json.dumps(R, indent=2))
print("wrote reference_values.json")
