#!/usr/bin/env python3
"""
Decomposition Learning Lab - EXERCISE A (Python)
================================================
How much of the household-language gap in ACCESS TO CARE is compositional?

Outcomes (NSCH-LC 2024 follow-up, children aged 6-17, baseline language known):
  (i)  PREVENTIVE_W2   at least one preventive visit in the past 12 months
                       (K4Q20R with the S4Q01 structural-zero rule, Trap 1)
  (ii) USUAL_SOURCE_W2 a usual place for sick care (K4Q01)

Methods, side by side:
  * twofold Oaxaca-Blinder on the LPM (English reference), Taylor CIs,
    Rubin-pooled over the 6 income implicates;
  * Fairlie (2005) logit decomposition with pooled coefficients, detailed
    block contributions over EVERY block ordering (120 orders), plus a PSU
    bootstrap (200 reps) of the aggregate explained part.

Covariate blocks (and why - read data-notes/exercise_a_covariates.md):
  demographics  AGE, SEX, RACE4, HISPANIC      who the child is (RACE4 = SC_RACE_R collapsed)
  ses           FPL (6 implicates), EDUCATION  family resources
  insurance     INSURED_W2 (CURRINS)          coverage - partly access itself
  health        FAIR_POOR_HEALTH_W2, SHCN_W2  need for care
  other_access  the OTHER access outcome      -> CIRCULAR: see spec B

Specifications per outcome:
  A  all five blocks
  B  without other_access   (circularity sensitivity: how much of the
                             "explained" share was access explaining access?)
  C  traps IN: dropped K4Q20R skips + CURRCOV  (falsification)

RUN:  python programs/exercise-a/exercise_a_access_gap.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "programs" / "lib"))
import labsvy as L                      # noqa: E402
import nschlc_prepare as P              # noqa: E402

# >>>>>>>>>>>>>>>>>>>>>>>> EDIT THIS ONE LINE IF NEEDED <<<<<<<<<<<<<<<<<<<<<<<<
DATA_PATH = ROOT / "data" / "nschlc_2024_puf.dta"
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
OUT = Path(__file__).resolve().parent / "output"
PP = 100.0
LOGS = []


def say(*x):
    s = " ".join(str(v) for v in x)
    print(s, flush=True)
    LOGS.append(s)


def add_vars(a):
    # K2Q01: 1=Excellent ... 5=Poor  -> fair/poor (4,5) = 1
    a["FAIR_POOR_HEALTH_W2"] = a.K2Q01_W2.map({1: 0., 2: 0., 3: 0., 4: 1., 5: 1.})
    # SC_CSHCN: 1=special health care needs, 2=no
    a["SHCN_W2"] = a.SC_CSHCN_W2.map({1: 1., 2: 0.})
    # SC_RACE_R has 6 categories; 3 (AIAN, n=71 aged 6-17) and 5 (NHPI, n=39)
    # are too sparse for a logit refitted in 200 bootstrap replicates
    # (a replicate where every drawn child has the outcome = perfect
    # separation). Collapse 3, 5, 7 into "other / multiple" for Exercise A.
    a["RACE4"] = a.RACE.map({1: 1, 2: 2, 4: 4, 3: 7, 5: 7, 7: 7})
    return a


def blocks_for(outcome, include_other_access=True, insured="INSURED_W2", preventive="PREVENTIVE_W2"):
    other = {"PREVENTIVE_W2": "USUAL_SOURCE_W2", "USUAL_SOURCE_W2": preventive}[outcome]
    b = {"demographics": ["AGE", "SEX", "RACE4", "HISPANIC"],
         "ses": ["FPL", "EDUCATION"],
         "insurance": [insured],
         "health": ["FAIR_POOR_HEALTH_W2", "SHCN_W2"]}
    if include_other_access:
        b["other_access"] = [other]
    return b


CATS = ["SEX", "RACE4", "HISPANIC", "EDUCATION"]


def matrices(a, blocks, lv):
    cols = [c for v in blocks.values() for c in v]
    cats = [c for c in cols if c in CATS]
    num = [c for c in cols if c not in cats]
    out = []
    for k in range(1, 7):
        d = a.copy()
        d["FPL"] = a[f"FPL{k}"]
        out.append(L.model_matrix(d, num, {c: lv[c] for c in cats}))
    return out


def run_spec(a, des, outcome, blocks, domain, lv, label, boot=True):
    g = (a.language2 == "English").to_numpy()
    y = a[outcome].to_numpy(float)
    Xs = matrices(a, blocks, lv)
    est, cov, fits = [], [], []
    for X in Xs:
        r = L.oaxaca(des, y, X, g, domain.to_numpy(), blocks)
        est.append(r["est"]); cov.append(des.covariance(r["infl"])); fits.append(r)
    pooled = L.rubin(est, cov, des.df - (len(fits[0]["bA"]) - 1))
    terms = fits[0]["terms"]
    keep = ["gap", "explained", "unexplained"] + [f"block:{b}" for b in blocks]
    lpm = {t: dict(est=pooled["est"][terms.index(t)] * PP, lo=pooled["lo"][terms.index(t)] * PP,
                   hi=pooled["hi"][terms.index(t)] * PP) for t in keep}
    # Fairlie, averaged over the 6 implicates. coef="A": ENGLISH logit
    # coefficients, the same reference as the LPM, so the two columns differ
    # only by model (linear vs logit). The pooled-logit version (no group
    # indicator) is reported separately: it changes the reference too.
    fr = [L.fairlie(y, X, des.w, g, domain.to_numpy(), blocks, coef="A") for X in Xs]
    frp = [L.fairlie(y, X, des.w, g, domain.to_numpy(), blocks, coef="pooled") for X in Xs]
    fair = dict(gap=np.mean([f["gap"] for f in fr]) * PP, explained=np.mean([f["explained"] for f in fr]) * PP,
                unexplained=np.mean([f["unexplained"] for f in fr]) * PP,
                sum_detail=np.mean([f["sum_detail"] for f in fr]) * PP, n_orders=fr[0]["n_orders"],
                detail={b: dict(mean=np.mean([f["detail"][b]["mean"] for f in fr]) * PP,
                                min=np.mean([f["detail"][b]["min"] for f in fr]) * PP,
                                max=np.mean([f["detail"][b]["max"] for f in fr]) * PP,
                                as_listed=np.mean([f["as_listed_order"][b] for f in fr]) * PP) for b in blocks},
                pooled_explained=np.mean([f["explained"] for f in frp]) * PP)
    if boot:
        # PSU bootstrap of the Fairlie AGGREGATE explained part (English logit
        # refitted in each replicate; Rubin within + between variance).
        rng = np.random.default_rng(L.SEED)
        ok = fits[0]["ok"]
        A, B = ok & g, ok & ~g
        reps = np.zeros((L.N_BOOT, 6))
        Xv = [X.to_numpy(float) for X in Xs]
        for bi in range(L.N_BOOT):
            w = des.w * L.rao_wu_factors(des, rng)
            for k in range(6):
                m = A & (w > 0)
                # a sparse dummy can be all-zero among drawn PSUs; it then has
                # no information (and no effect on weighted means) -> drop it
                c = (Xv[k][m] != 0).any(axis=0)
                b_, _ = L.wlogit(y[m], Xv[k][m][:, c], w[m])
                F = 1 / (1 + np.exp(-(Xv[k][:, c] @ b_)))
                reps[bi, k] = np.average(F[A], weights=w[A]) - np.average(F[B], weights=w[B])
        W = np.mean(np.var(reps, axis=0, ddof=1))
        Bv = np.var([f["explained"] for f in fr], ddof=1)
        se = np.sqrt(W + (1 + 1 / 6) * Bv)
        e = np.mean([f["explained"] for f in fr])
        fair["explained_lo"], fair["explained_hi"] = (e - 1.96 * se) * PP, (e + 1.96 * se) * PP
    say(f"\n--- {label}: n={fits[0]['n']} (English {fits[0]['nA']}, other-language {fits[0]['nB']})")
    say(f"{'':28s}{'LPM Oaxaca (95% CI)':>30s}   {'Fairlie, English logit: mean over orders [min, max]':>52s}")
    for t in ["gap", "explained", "unexplained"]:
        fv = fair[t]
        extra = f"  ({fair['explained_lo']:.2f}, {fair['explained_hi']:.2f})" if (t == "explained" and boot) else ""
        say(f"{t:28s}{lpm[t]['est']:8.2f} ({lpm[t]['lo']:7.2f},{lpm[t]['hi']:7.2f})   {fv:8.2f}{extra}")
    for b in blocks:
        d = fair["detail"][b]
        say(f"{'block:' + b:28s}{lpm['block:' + b]['est']:8.2f} ({lpm['block:' + b]['lo']:7.2f},{lpm['block:' + b]['hi']:7.2f})"
            f"   {d['mean']:8.2f} [{d['min']:6.2f}, {d['max']:6.2f}]  as-listed {d['as_listed']:6.2f}")
    say(f"{'Fairlie explained, POOLED logit (no group indicator; different reference)':74s} {fair['pooled_explained']:8.2f}")
    share = lpm["explained"]["est"] / lpm["gap"]["est"]
    say(f"LPM explained share {share:.1%}  |  Fairlie explained share {fair['explained'] / fair['gap']:.1%}"
        "   ('explained' = compositional, not causal)")
    return dict(n=fits[0]["n"], n_english=fits[0]["nA"], n_other=fits[0]["nB"], lpm=lpm, fairlie=fair, ok=fits[0]["ok"],
                lpm_share=share, fairlie_share=fair["explained"] / fair["gap"])


def synthetic_dry_run():
    """Fairlie machinery on data with a KNOWN answer: if the outcome does not
    depend on x at all (true logit slope 0), every explained part must be ~0
    and Fairlie's explained must equal the LPM's (both 0)."""
    rng = np.random.default_rng(L.SEED)
    n = 8000
    g = np.r_[np.ones(5000, bool), np.zeros(3000, bool)]
    x = np.r_[rng.normal(1, 1, 5000), rng.normal(0, 1, 3000)]
    # outcome depends on group only, exactly balanced within each group
    y = np.r_[np.tile([1, 0, 0, 0, 0], 1000), np.tile([1, 0, 0], 1000)].astype(float)
    X = pd.DataFrame({"Intercept": 1.0, "x": x})
    d = L.Design(np.ones(n), np.repeat(np.arange(40), n // 40), np.arange(n))
    r = L.oaxaca(d, y, X, g, np.ones(n, bool), {"x": ["x"]})
    f = L.fairlie(y, X, np.ones(n), g, np.ones(n, bool), {"x": ["x"]}, coef="A")
    fp = L.fairlie(y, X, np.ones(n), g, np.ones(n, bool), {"x": ["x"]}, coef="pooled")
    e = dict(zip(r["terms"], r["est"]))
    say(f"synthetic: gap {e['gap']:.4f} (true {0.2 - 1/3:.4f}); LPM explained {e['explained']:.4f}; "
        f"Fairlie explained, English logit {f['explained']:.4f}, pooled logit {fp['explained']:.4f}  "
        "(English-reference values near 0 because y does not depend on x within group)")
    ok = abs(e["gap"] - (0.2 - 1 / 3)) < 1e-12 and abs(e["explained"]) < 0.02 and abs(f["explained"]) < 0.02
    say("synthetic dry run:", "PASS" if ok else "FAIL")
    if not ok:
        raise SystemExit("Synthetic dry run failed")
    return dict(gap=e["gap"], lpm_explained=e["explained"], fairlie_explained=f["explained"], passed=ok)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    R = {"synthetic": synthetic_dry_run()}
    a = add_vars(P.prepare(P.obtain(DATA_PATH)))
    des = L.nsch_lc_design(a)
    lv = {c: L.levels_of(a[c]) for c in CATS}
    dom = a.AGE.between(6, 17) & a.language2.notna()
    R["specs"] = {}
    for outcome in ["PREVENTIVE_W2", "USUAL_SOURCE_W2"]:
        say("\n" + "=" * 78 + f"\nOUTCOME {outcome}\n" + "=" * 78)
        sA = run_spec(a, des, outcome, blocks_for(outcome), dom, lv, "A: all blocks (incl. other access)")
        okA = pd.Series(sA.pop("ok"), index=a.index)
        R["specs"][f"{outcome}|A_all_blocks"] = sA
        # B on the SAME children as A (Module 5: only a same-case comparison
        # isolates the covariate; the gap must be identical to A's)
        sB = run_spec(a, des, outcome, blocks_for(outcome, False), dom & okA, lv,
                      "B: without the other access variable, same children as A")
        sB.pop("ok")
        R["specs"][f"{outcome}|B_no_other_access"] = sB
        # C: traps IN. Outcome and covariates built the WRONG way.
        a_wrong = a.copy()
        a_wrong["PREVENTIVE_W2"] = a_wrong["PREVENTIVE_DROPSKIP_W2"]
        a_wrong["INSURED_W2"] = a_wrong["INSURED_CURRCOV_W2"]
        sC = run_spec(a_wrong, des, outcome, blocks_for(outcome), dom, lv,
                      "C: TRAPS IN (K4Q20R skips dropped, CURRCOV)", boot=False)
        sC.pop("ok")
        R["specs"][f"{outcome}|C_traps_in"] = sC
    # self-check: the descriptive gaps must match the core study's logged values
    ref = json.loads((ROOT / "data-notes" / "reference_values.json").read_text())["descriptives"]
    checks = []
    for outcome, key in [("PREVENTIVE_W2", "preventive"), ("USUAL_SOURCE_W2", "usual")]:
        want = ref[f"{key}_english"]["est"] - ref[f"{key}_other"]["est"]
        got = R["specs"][f"{outcome}|A_all_blocks"]["lpm"]["gap"]["est"]
        # the complete-case gap differs from the all-available descriptive gap
        checks.append(dict(figure=f"{outcome} complete-case gap vs descriptive gap (info only)", computed=got, reference=want))
        say(f"[INFO] {outcome}: complete-case gap {got:.2f} pp vs all-available descriptive gap {want:.2f} pp "
            "(different samples: decomposition requires complete covariates)")
    for outcome in ["PREVENTIVE_W2", "USUAL_SOURCE_W2"]:
        s = R["specs"][f"{outcome}|A_all_blocks"]
        ident = abs(s["lpm"]["gap"]["est"] - s["lpm"]["explained"]["est"] - s["lpm"]["unexplained"]["est"])
        bsum = abs(sum(s["lpm"][f"block:{b}"]["est"] for b in blocks_for(outcome)) - s["lpm"]["explained"]["est"])
        for nm, v in [("LPM identity", ident), ("LPM blocks sum to explained", bsum)]:
            checks.append(dict(figure=f"{outcome} {nm}", computed=v, reference=0, result="PASS" if v < 1e-9 else "FAIL"))
            say(f"[{'PASS' if v < 1e-9 else 'FAIL'}] {outcome} {nm}: {v:.2e}")
    # B is same-case: n and gap must equal A's exactly
    for outcome in ["PREVENTIVE_W2", "USUAL_SOURCE_W2"]:
        sa, sb = R["specs"][f"{outcome}|A_all_blocks"], R["specs"][f"{outcome}|B_no_other_access"]
        v = abs(sa["lpm"]["gap"]["est"] - sb["lpm"]["gap"]["est"]) + abs(sa["n"] - sb["n"])
        checks.append(dict(figure=f"{outcome} spec B same children as A (|gap diff| + |n diff|)", computed=v, reference=0,
                           result="PASS" if v < 1e-9 else "FAIL"))
        say(f"[{'PASS' if v < 1e-9 else 'FAIL'}] {outcome} spec B uses the same children as A: {v:.2e}")
    # independent check: the domain means of both outcomes, recomputed here,
    # against the reviewed pipeline's logged descriptives (±0.05 pp)
    for var, key in [("PREVENTIVE_W2", "preventive"), ("USUAL_SOURCE_W2", "usual")]:
        for gname, gm in (("english", a.language2 == "English"), ("other", a.language2 == "Non-English")):
            m = des.mean(a[var], dom & gm)
            got, want = m["est"] * PP, ref[f"{key}_{gname}"]["est"]
            res = "PASS" if abs(got - want) <= 0.05 else "FAIL"
            checks.append(dict(figure=f"{key}_{gname} vs logged reference", computed=got, reference=want, result=res))
            say(f"[{res}] {key}_{gname}: {got:.4f} vs logged {want:.4f} (tol ±0.05)")
    # falsification: trap-in spec must MOVE the preventive gap
    mv = R["specs"]["PREVENTIVE_W2|C_traps_in"]["lpm"]["gap"]["est"] - R["specs"]["PREVENTIVE_W2|A_all_blocks"]["lpm"]["gap"]["est"]
    say(f"[{'PASS' if abs(mv) > 1 else 'FAIL'}] falsification: traps-in changes the preventive-visit gap by {mv:.2f} pp "
        "(if ~0, your code is not applying the S4Q01 structural-zero rule)")
    checks.append(dict(figure="traps-in moves preventive gap (pp)", computed=mv, result="PASS" if abs(mv) > 1 else "FAIL"))
    R["self_check"] = checks
    (OUT / "exercise_a_results.json").write_text(json.dumps(R, indent=2, default=float))
    (OUT / "exercise_a_run_log.txt").write_text("\n".join(LOGS) + "\n")
    return 0 if all(c.get("result", "PASS") == "PASS" for c in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
