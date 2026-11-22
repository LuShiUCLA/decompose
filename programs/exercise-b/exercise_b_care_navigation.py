#!/usr/bin/env python3
"""
Decomposition Learning Lab - EXERCISE B (Python)
================================================
Among publicly insured children with special health care needs (CSHCN) who
needed help coordinating their care, how much of the household-language gap
in EFFECTIVE CARE NAVIGATION (versus unmet need) is compositional?

Why the annual NSCH (2016-2025) and not the NSCH-LC file: the coordination
items K5Q20_R, K5Q21, K5Q22 are marked 'N' for 2024 in the NSCH-LC Variable
List (data-notes/codebook_excerpts.md): they were not fielded at follow-up.

Population (each step logged in the sample flow):
  CSHCN          SC_CSHCN = 1
  public cover   INSTYPE in (1 public only, 3 private and public): Medicaid,
                 CHIP or another government assistance plan. The public-use
                 file does not separate Medicaid from other public plans, so
                 this is 'publicly insured', not strictly 'Medicaid-enrolled'.
  need           K5Q20_R = 1 (someone helped coordinate) or K5Q21 = 1 (could
                 have used extra help): an established coordination need.

Outcome (builder's definition from the questionnaire routing; documented in
data-notes/exercise_b_outcome.md):
  NAVIGATED = 1  need met: K5Q21 = 2 (no extra help needed) or
                 K5Q22 = 1 (usually got as much help as wanted)
  NAVIGATED = 0  unmet need: K5Q21 = 1 and K5Q22 in (2 sometimes, 3 never)
  K5Q22 is SKIPPED when K5Q21 = 2. As in Trap 1, that skip carries
  information (no extra help was needed), it is not missing.

Methods:
  1. Twofold Oaxaca-Blinder on the LPM, English reference, year fixed
     effects as their own block, Taylor variance on the pooled design,
     Rubin's rules over the six FPL implicates.
  2. DiNardo-Fortin-Lemieux (1996) reweighting: English children are
     reweighted to the other-language covariate distribution with a pooled
     logit; explained = English mean - reweighted English mean. Same
     counterfactual as (1) without assuming a linear outcome model. PSU
     bootstrap (Rao-Wu, 200 replicates) + Rubin.
  Falsification: leave-one-year-out; 2016-2021 (re-released with revised
  weights) vs 2022-2025; and the skip trap (K5Q22 skip treated as missing).

Pooled design (NSCH Guide to Multi-Year Estimates, Census, Oct 2025):
  weight FWC / number of years; strata FIPSST x STRATUM with '2A' recoded to
  '2'; PSU HHID (HHIDs are unique across years: they start with the year).
  Use only the enhanced 'e' files (the guide says so; they are the only
  files Census now posts for 2016-2021).

RUN from the repository root:  python programs/exercise-b/exercise_b_care_navigation.py
"""
from __future__ import annotations

import json
import sys
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "programs" / "lib"))
import labsvy as L                      # noqa: E402

# >>>>>>>>>>>>>>>>>>>>>>>> EDIT THIS ONE LINE IF NEEDED <<<<<<<<<<<<<<<<<<<<<<<<
ANNUAL_DIR = ROOT / "data" / "annual_nsch"
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
OUT = Path(__file__).resolve().parent / "output"
YEARS = list(range(2016, 2026))
BASE = "https://www2.census.gov/programs-surveys/nsch/datasets"
PP = 100.0
LOGS = []

BLOCKS = {"demographics": ["AGE", "SEX", "RACE4", "HISPANIC"],
          "ses": ["FPL", "EDUCATION"],
          "coverage": ["PUBLIC_AND_PRIVATE"],
          "health": ["FAIR_POOR_HEALTH"],
          "usual_source": ["USUAL_SOURCE"],
          "survey_year": ["YEAR"]}
CATS = ["SEX", "RACE4", "HISPANIC", "EDUCATION", "YEAR"]


def say(*x):
    s = " ".join(str(v) for v in x)
    print(s, flush=True)
    LOGS.append(s)


def stem(y):
    return f"nsch_{y}e_topical"


def obtain(y):
    """Return the year's .dta path; download and extract the Census zip if absent."""
    dta = ANNUAL_DIR / f"{stem(y)}.dta"
    if dta.exists():
        return dta
    ANNUAL_DIR.mkdir(parents=True, exist_ok=True)
    zname = "nsch_2023e_topical_Stata.zip" if y == 2023 else f"nsch_{y}_topical_Stata.zip"
    z = ANNUAL_DIR / zname
    if not z.exists():
        url = f"{BASE}/{y}/{zname}"
        say(f"Downloading {url}")
        req = urllib.request.Request(url, headers={"User-Agent": "decomposition-learning-lab"})
        with urllib.request.urlopen(req, timeout=300) as r, open(z.with_suffix(".part"), "wb") as f:
            while chunk := r.read(1 << 20):
                f.write(chunk)
        z.with_suffix(".part").replace(z)
    with zipfile.ZipFile(z) as zf:
        dta.write_bytes(zf.read(f"{stem(y)}.dta"))
    return dta


NEED_COLS = ["hhid", "fipsst", "stratum", "fwc", "hhlanguage", "k5q20_r", "k5q21", "k5q22",
             "instype", "sc_cshcn", "sc_age_years", "sc_sex", "sc_race_r", "sc_hispanic_r",
             "higrade_tvis", "k2q01", "k4q01"] + [f"fpl_i{k}" for k in range(1, 7)]


ORIGINAL_YEARS = [2016, 2017, 2018]


def original_weights():
    """FWC from the un-suffixed 2016-2018 files that Census still posts next to
    the enhanced ones (nsch_<year>_topical.dta). They carry the ORIGINAL,
    pre-revision weights: every FWC differs from the enhanced file, and they
    still contain race code 6 ('some other race'), which the revision imputed.
    Used only for the weight-revision falsification check."""
    out = []
    for y in ORIGINAL_YEARS:
        f = ANNUAL_DIR / "original" / f"nsch_{y}_topical.dta"
        if not f.exists():
            f.parent.mkdir(parents=True, exist_ok=True)
            url = f"{BASE}/{y}/nsch_{y}_topical.dta"
            say(f"Downloading {url}")
            req = urllib.request.Request(url, headers={"User-Agent": "decomposition-learning-lab"})
            with urllib.request.urlopen(req, timeout=300) as r, open(f.with_suffix(".part"), "wb") as fh:
                while chunk := r.read(1 << 20):
                    fh.write(chunk)
            f.with_suffix(".part").replace(f)
        d = pd.read_stata(f, columns=None, convert_categoricals=False)
        d.columns = d.columns.str.lower()
        out.append(d[["hhid", "fwc"]].rename(columns={"fwc": "fwc_original"}))
    return pd.concat(out, ignore_index=True)


def prepare():
    """Harmonised pooled file. Each recode below is logged, with its reason,
    in data-notes/exercise_b_harmonisation.md (built from the Census .do files)."""
    frames = []
    for y in YEARS:
        d = pd.read_stata(obtain(y), convert_categoricals=False)
        d.columns = d.columns.str.lower()
        d = d[NEED_COLS].copy()
        d["YEAR"] = y
        frames.append(d)
    a = pd.concat(frames, ignore_index=True)
    a["W_POOL"] = a.fwc / len(YEARS)                       # average annual weight (multi-year guide)
    s = a.stratum.astype(str).str.upper().replace({"2A": "2"})  # 2016 had strata 1, 2; later 1, 2A
    a["STRATA"] = a.fipsst.astype(int).astype(str) + "_" + s
    a["PSU"] = a.hhid.astype("int64").astype(str)
    a["language"] = a.hhlanguage.map({1: "English", 2: "Other", 3: "Other"})
    a["language3"] = a.hhlanguage.map({1: "English", 2: "Spanish", 3: "Other non-English"})
    a["CSHCN"] = a.sc_cshcn == 1
    a["PUBLIC"] = a.instype.isin([1, 3])
    a["NEED"] = (a.k5q20_r == 1) | (a.k5q21 == 1)
    # Outcome. K5Q22 is asked only when K5Q21 = 1; K5Q21 = 2 means no extra
    # help was needed, so the need is met (NAVIGATED = 1), not missing.
    nav = pd.Series(np.nan, index=a.index)
    nav[a.k5q21 == 2] = 1.0
    nav[(a.k5q21 == 1) & (a.k5q22 == 1)] = 1.0
    nav[(a.k5q21 == 1) & a.k5q22.isin([2, 3])] = 0.0
    a["NAVIGATED"] = nav.where(a.NEED)
    # The TRAP version: K5Q22's skip treated as missing (drops every child
    # whose need was met without extra help).
    a["NAVIGATED_DROPSKIP"] = a.k5q22.map({1: 1.0, 2: 0.0, 3: 0.0}).where(a.NEED)
    a["AGE"] = a.sc_age_years.astype(float)
    a["SEX"] = a.sc_sex.where(a.sc_sex.isin([1, 2]))
    # SC_RACE_R: 3 (AI/AN) and 5 (NHPI) are sparse in this population; code 6
    # ('some other race') is labelled for 2016-2018 but does not occur in the
    # enhanced files. Collapse 3, 5, 6, 7 to 7 = other or multiple races.
    a["RACE4"] = a.sc_race_r.map({1: 1, 2: 2, 4: 4, 3: 7, 5: 7, 6: 7, 7: 7})
    a["HISPANIC"] = a.sc_hispanic_r.where(a.sc_hispanic_r.isin([1, 2]))
    a["EDUCATION"] = a.higrade_tvis.where(a.higrade_tvis.isin([1, 2, 3, 4]))
    a["PUBLIC_AND_PRIVATE"] = (a.instype == 3).astype(float).where(a.instype.isin([1, 3]))
    a["FAIR_POOR_HEALTH"] = a.k2q01.map({1: 0., 2: 0., 3: 0., 4: 1., 5: 1.})
    a["USUAL_SOURCE"] = a.k4q01.map({1: 1., 2: 0.})
    for k in range(1, 7):                                  # FPL in units of 100% of poverty
        a[f"FPL{k}"] = a[f"fpl_i{k}"] / 100.0
    return a


def matrices(a, lv):
    cols = [c for v in BLOCKS.values() for c in v]
    num = [c for c in cols if c not in CATS]
    out = []
    for k in range(1, 7):
        d = a.copy()
        d["FPL"] = a[f"FPL{k}"]
        out.append(L.model_matrix(d, num, {c: lv[c] for c in CATS}))
    return out


def dfl_point(y, Xv, w, E, O, ok):
    """DFL reweighting (English reference). Logit of P(other | X) on the
    analysis sample; English children get psi = p/(1-p) (the constant
    sum(wE)/sum(wO) cancels in the weighted mean). Returns gap, explained,
    unexplained, and diagnostics of the reweighting factors."""
    m = ok & (w > 0)
    c = (Xv[m] != 0).any(axis=0)                           # drop all-zero dummies (bootstrap)
    b, _ = L.wlogit(O[m].astype(float), Xv[m][:, c], w[m])
    p = 1 / (1 + np.exp(-(Xv[:, c] @ b)))
    A, B = m & E, m & O
    psi = p / (1 - p)
    yE, yO = np.average(y[A], weights=w[A]), np.average(y[B], weights=w[B])
    yEc = np.average(y[A], weights=w[A] * psi[A])
    ww = w[A] * psi[A]
    return dict(gap=yE - yO, explained=yE - yEc, unexplained=yEc - yO, counterfactual=yEc,
                ess=float(ww.sum() ** 2 / (ww ** 2).sum()), max_share=float(ww.max() / ww.sum()))


def synthetic_dry_run():
    """Known answer: x differs by 1 between groups, y = 0.3 + 0.1 x + noise in
    BOTH groups (same structure), x normal with equal variances so the logit
    P(group | x) is correctly specified. Both methods must give explained =
    gap = 0.1 (to sampling error) and unexplained ~ 0."""
    rng = np.random.default_rng(L.SEED)
    n = 20000
    x = np.r_[rng.normal(1, 1, n), rng.normal(0, 1, n)]
    E = np.r_[np.ones(n, bool), np.zeros(n, bool)]
    y = 0.3 + 0.1 * x + rng.normal(0, 0.05, 2 * n)
    X = pd.DataFrame({"Intercept": 1.0, "x": x})
    d = L.Design(np.ones(2 * n), np.repeat(np.arange(40), 2 * n // 40), np.arange(2 * n))
    r = dict(zip(*(lambda o: (o["terms"], o["est"]))(L.oaxaca(d, y, X, E, np.ones(2 * n, bool)))))
    f = dfl_point(y, X.to_numpy(), np.ones(2 * n), E, ~E, np.ones(2 * n, bool))
    say(f"synthetic: gap {r['gap']:.4f}; Oaxaca explained {r['explained']:.4f}; DFL explained {f['explained']:.4f}; "
        f"DFL unexplained {f['unexplained']:.4f} (true explained 0.1, unexplained 0)")
    ok = abs(r["explained"] - 0.1) < 0.01 and abs(f["explained"] - 0.1) < 0.01 and abs(f["unexplained"]) < 0.01
    say("synthetic dry run:", "PASS" if ok else "FAIL")
    if not ok:
        raise SystemExit("Synthetic dry run failed")
    return dict(oaxaca_explained=r["explained"], dfl_explained=f["explained"], dfl_unexplained=f["unexplained"], passed=ok)


def oaxaca_pooled(des, y, Xs, E, keep):
    est, cov, fits = [], [], []
    for X in Xs:
        r = L.oaxaca(des, y, X, E, keep, BLOCKS)
        est.append(r["est"]); cov.append(des.covariance(r["infl"])); fits.append(r)
    pooled = L.rubin(est, cov, des.df - (len(fits[0]["bA"]) - 1))
    terms = fits[0]["terms"]
    keep_t = ["gap", "explained", "unexplained"] + [f"block:{b}" for b in BLOCKS]
    out = {t: dict(est=pooled["est"][terms.index(t)] * PP, lo=pooled["lo"][terms.index(t)] * PP,
                   hi=pooled["hi"][terms.index(t)] * PP) for t in keep_t}
    return out, fits


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    R = {"synthetic": synthetic_dry_run()}
    say("\nSTEP 1  Load and harmonise ten annual files")
    a = prepare()
    des = L.Design(a.W_POOL, a.STRATA, a.PSU)
    say(f"children={len(a)}  strata={des.n_strata}  PSUs={des.n_psu}  design df={des.df}")
    R["design"] = dict(children=len(a), strata=des.n_strata, psus=des.n_psu, df=des.df)

    flow = {}
    steps = [("all children", np.ones(len(a), bool)), ("CSHCN", a.CSHCN.to_numpy()),
             ("and publicly insured", (a.CSHCN & a.PUBLIC).to_numpy()),
             ("and coordination need", (a.CSHCN & a.PUBLIC & a.NEED).to_numpy()),
             ("and household language known", (a.CSHCN & a.PUBLIC & a.NEED & a.language.notna()).to_numpy()),
             ("and outcome known", (a.CSHCN & a.PUBLIC & a.NEED & a.language.notna() & a.NAVIGATED.notna()).to_numpy())]
    for nm, m in steps:
        flow[nm] = int(m.sum())
        say(f"  sample flow: {nm:32s} {m.sum():7d}")
    by_year = {int(y): int(((a.YEAR == y).to_numpy() & steps[-1][1]).sum()) for y in YEARS}
    say("  analysis sample by year:", by_year)
    R["sample_flow"] = flow
    R["sample_by_year"] = by_year

    dom = (a.CSHCN & a.PUBLIC & a.NEED & a.language.notna()).to_numpy()
    E = (a.language == "English").to_numpy()
    O = (a.language == "Other").to_numpy()
    y = a.NAVIGATED.to_numpy(float)

    say("\nSTEP 2  Descriptives (domain estimation on the full pooled design)")
    D = {}
    for nm, g in [("english", a.language == "English"), ("other", a.language == "Other"),
                  ("spanish", a.language3 == "Spanish"), ("other_nonenglish", a.language3 == "Other non-English")]:
        m = des.mean(a.NAVIGATED, dom & g.to_numpy(), proportion=True)
        D[f"navigated_{nm}"] = dict(est=m["est"] * PP, lo=m["lo"] * PP, hi=m["hi"] * PP, n=m["n"])
        say(f"  navigated, {nm:16s} {m['est']*PP:6.2f} ({m['lo']*PP:.2f}, {m['hi']*PP:.2f}) n={m['n']}")
    R["descriptives"] = D

    say("\nSTEP 3  Oaxaca-Blinder (LPM, English reference, year fixed effects)")
    lv = {c: L.levels_of(a.loc[dom, c]) for c in CATS}
    Xs = matrices(a, lv)
    ox, fits = oaxaca_pooled(des, y, Xs, E, dom)
    ok = fits[0]["ok"]
    say(f"  n = {fits[0]['n']} (English {fits[0]['nA']}, other-language {fits[0]['nB']})")
    for t, v in ox.items():
        say(f"  {t:24s} {v['est']:7.2f} ({v['lo']:6.2f}, {v['hi']:6.2f})")
    R["oaxaca"] = dict(n=fits[0]["n"], n_english=fits[0]["nA"], n_other=fits[0]["nB"], terms=ox,
                       outside01_english=[f["out01A"] for f in fits], outside01_other=[f["out01B"] for f in fits])

    say("\nSTEP 4  DFL reweighting, PSU bootstrap (Rao-Wu, 200 replicates)")
    Xv = [X.to_numpy(float) for X in Xs]
    pts = [dfl_point(y, X, des.w, E, O, ok) for X in Xv]
    rng = np.random.default_rng(L.SEED)
    reps = np.zeros((L.N_BOOT, 6, 3))
    for bi in range(L.N_BOOT):
        wb = des.w * L.rao_wu_factors(des, rng)
        for k in range(6):
            r = dfl_point(y, Xv[k], wb, E, O, ok)
            reps[bi, k] = [r["gap"], r["explained"], r["unexplained"]]
    dfl = {}
    for j, t in enumerate(["gap", "explained", "unexplained"]):
        q = np.array([p[t] for p in pts])
        W = np.mean(np.var(reps[:, :, j], axis=0, ddof=1))
        se = np.sqrt(W + (1 + 1 / 6) * np.var(q, ddof=1))
        dfl[t] = dict(est=q.mean() * PP, lo=(q.mean() - 1.96 * se) * PP, hi=(q.mean() + 1.96 * se) * PP, se=se * PP)
        say(f"  DFL {t:12s} {dfl[t]['est']:7.2f} ({dfl[t]['lo']:6.2f}, {dfl[t]['hi']:6.2f})")
    dfl["ess_english_reweighted"] = float(np.mean([p["ess"] for p in pts]))
    dfl["max_weight_share"] = float(np.max([p["max_share"] for p in pts]))
    say(f"  reweighted English effective sample size {dfl['ess_english_reweighted']:.0f} of {fits[0]['nA']}; "
        f"largest single-child weight share {dfl['max_weight_share']:.4f}")
    R["dfl"] = dfl

    say("\nSTEP 5  Falsification")
    F = {}
    # (a) leave one year out: point estimates, implicate-averaged
    loyo = {}
    def sub_matrices(years):
        # year dummies only for the years kept (a dummy that is 0 for every
        # analysed child would make the regression singular)
        lv_ = dict(lv, YEAR=[v for v in lv["YEAR"] if v in years])
        return matrices(a, lv_)
    for yr in YEARS:
        keep = dom & (a.YEAR != yr).to_numpy()
        Xy = sub_matrices([v for v in YEARS if v != yr])
        ests = [dict(zip(r["terms"], r["est"])) for r in (L.oaxaca(des, y, X, E, keep, BLOCKS) for X in Xy)]
        okk = ok & keep
        d_ = [dfl_point(y, X.to_numpy(float), des.w, E, O, okk) for X in Xy]
        loyo[str(yr)] = dict(gap=np.mean([e["gap"] for e in ests]) * PP,
                             oaxaca_explained=np.mean([e["explained"] for e in ests]) * PP,
                             dfl_explained=np.mean([d["explained"] for d in d_]) * PP)
        say(f"  without {yr}: gap {loyo[str(yr)]['gap']:6.2f}  Oaxaca explained {loyo[str(yr)]['oaxaca_explained']:6.2f}"
            f"  DFL explained {loyo[str(yr)]['dfl_explained']:6.2f}")
    F["leave_one_year_out"] = loyo
    # (b) the 2016-2021 files were re-released with revised weights; compare
    # the two periods (domain estimation on the full pooled design)
    per = {}
    for nm, yrs in [("2016_2021_rereleased", range(2016, 2022)), ("2022_2025", range(2022, 2026))]:
        keep = dom & a.YEAR.isin(list(yrs)).to_numpy()
        o, f_ = oaxaca_pooled(des, y, sub_matrices(list(yrs)), E, keep)
        per[nm] = dict(n=f_[0]["n"], gap=o["gap"], explained=o["explained"], unexplained=o["unexplained"])
        say(f"  {nm:22s} n={f_[0]['n']:6d} gap {o['gap']['est']:6.2f} ({o['gap']['lo']:.2f}, {o['gap']['hi']:.2f})"
            f"  explained {o['explained']['est']:6.2f} ({o['explained']['lo']:.2f}, {o['explained']['hi']:.2f})")
    F["period_split"] = per
    # (c) weight revision: 2016-2018 with original vs enhanced weights
    ow = original_weights()
    a2 = a[["hhid"]].merge(ow, on="hhid", how="left")
    w_orig = np.where(a2.fwc_original.notna().to_numpy(), a2.fwc_original.to_numpy() / len(YEARS), des.w)
    des_o = L.Design(w_orig, a.STRATA, a.PSU)
    keep = dom & a.YEAR.isin(ORIGINAL_YEARS).to_numpy()
    Xo = sub_matrices(ORIGINAL_YEARS)
    rev = {}
    for nm, dd in [("enhanced_weights", des), ("original_weights", des_o)]:
        o, f_ = oaxaca_pooled(dd, y, Xo, E, keep)
        rev[nm] = dict(n=f_[0]["n"], gap=o["gap"], explained=o["explained"], unexplained=o["unexplained"])
        say(f"  2016-2018, {nm:17s} n={f_[0]['n']:5d} gap {o['gap']['est']:6.2f} ({o['gap']['lo']:.2f}, {o['gap']['hi']:.2f})"
            f"  explained {o['explained']['est']:6.2f} ({o['explained']['lo']:.2f}, {o['explained']['hi']:.2f})")
    rev["matched_original_weights"] = int(a2.fwc_original.notna().sum())
    F["weight_revision_2016_2018"] = rev
    # (d) the skip trap
    ytrap = a.NAVIGATED_DROPSKIP.to_numpy(float)
    t_, ft = oaxaca_pooled(des, ytrap, Xs, E, dom)
    mt = des.mean(a.NAVIGATED_DROPSKIP, dom & E, proportion=True)
    mo = des.mean(a.NAVIGATED_DROPSKIP, dom & O, proportion=True)
    F["skip_trap"] = dict(n=ft[0]["n"], gap=t_["gap"], explained=t_["explained"],
                          navigated_english=mt["est"] * PP, navigated_other=mo["est"] * PP)
    say(f"  skip trap (K5Q22 skip as missing): n={ft[0]['n']} navigated English {mt['est']*PP:.2f}% vs other {mo['est']*PP:.2f}%;"
        f" gap {t_['gap']['est']:.2f} pp (correct coding: n={fits[0]['n']}, gap {ox['gap']['est']:.2f} pp)")
    R["falsification"] = F

    say("\nSELF-CHECK")
    checks = []

    def chk(name, val, ref, tol):
        res = "PASS" if abs(val - ref) <= tol else "FAIL"
        checks.append(dict(figure=name, computed=val, reference=ref, tol=tol, result=res))
        say(f"[{res}] {name:58s} computed {val:10.4f}  reference {ref:10.4f}  tol ±{tol:g}")
    chk("Oaxaca identity: gap - explained - unexplained", ox["gap"]["est"] - ox["explained"]["est"] - ox["unexplained"]["est"], 0, 1e-9)
    chk("Oaxaca blocks sum to explained", sum(ox[f"block:{b}"]["est"] for b in BLOCKS) - ox["explained"]["est"], 0, 1e-9)
    chk("DFL identity: gap - explained - unexplained", dfl["gap"]["est"] - dfl["explained"]["est"] - dfl["unexplained"]["est"], 0, 1e-9)
    chk("DFL gap equals Oaxaca gap (same sample)", dfl["gap"]["est"], ox["gap"]["est"], 1e-9)
    chk("No singleton strata in the pooled design", des.singletons, 0, 0)
    moved = abs(F["skip_trap"]["n"] - fits[0]["n"])
    res = "PASS" if moved > 0 else "FAIL"
    checks.append(dict(figure="skip trap changes the analysed n", computed=moved, result=res))
    say(f"[{res}] skip trap changes the analysed n by {moved} children (if 0, your code is not reading K5Q21)")
    R["self_check"] = checks
    nf = sum(c["result"] == "FAIL" for c in checks)
    say(f"\nSELF-CHECK: {len(checks) - nf} PASS, {nf} FAIL")
    (OUT / "exercise_b_results.json").write_text(json.dumps(R, indent=2, default=float))
    (OUT / "exercise_b_run_log.txt").write_text("\n".join(LOGS) + "\n")
    return 0 if nf == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
