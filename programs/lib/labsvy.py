"""labsvy: the small, fully commented survey + decomposition toolkit used by
every Python program in this lab (core study, Exercise A, Exercise B).

Why a hand-written toolkit instead of a black-box package?
  * Python has no maintained package that does design-based (Taylor) variance
    for an Oaxaca-Blinder decomposition on survey data. Writing the ~300 lines
    ourselves lets a learner read every step, and lets the R twin
    (programs/lib/labsvy.R) reproduce the same numbers independently.
  * The design rules follow the Census NSCH-LC Source and Accuracy Statement
    (4 Aug 2026), pp. 6-7: Taylor series, strata = FIPSSTO x STRATUM (2A
    collapsed to 2), PSU = HHID, weight = FWC, households treated as sampled
    with replacement.

Conventions
  * Every estimator returns an *influence* vector of length N_full (one value
    per row of the FULL respondent file, zero outside the analysis domain).
    The Taylor variance is then computed from PSU totals of the influences
    within strata. Keeping the zero rows is what makes this "domain
    estimation" rather than "subsetting" (lab Module 3).
  * Proportions are on the 0-1 scale inside this file; programs convert to
    percentage points (pp) for display.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

SEED = 20261117          # bootstrap seed used throughout the lab (Section 5.3)
N_BOOT = 200             # bootstrap replicates (Section 5.3)


# ---------------------------------------------------------------------------
# 1. The survey design
# ---------------------------------------------------------------------------
class Design:
    """Full-frame stratified, clustered, weighted design (with-replacement).

    lonely: what to do with a stratum that has only ONE PSU.
      'fail'   -> raise (the full NSCH-LC frame has none; a singleton can only
                  appear if you wrongly pre-subset the file);
      'remove' -> the singleton stratum contributes zero variance
                  (like R survey lonely.psu='remove' / 'certainty');
      'adjust' -> centre the singleton PSU at the grand mean instead of its
                  stratum mean, so it contributes variance
                  (like R survey lonely.psu='adjust').
    """

    def __init__(self, weights, strata, psu, lonely="fail"):
        self.w = np.asarray(weights, float)
        if not (np.isfinite(self.w).all() and (self.w > 0).all()):
            raise ValueError("weights must be finite and positive")
        keys = pd.MultiIndex.from_arrays([pd.Series(strata).astype(str).values,
                                          pd.Series(psu).astype(str).values])
        self.psu_code, ukeys = pd.factorize(keys, sort=True)
        self.n_psu = len(ukeys)
        self.psu_stratum, ustrata = pd.factorize(ukeys.get_level_values(0), sort=True)
        self.n_strata = len(ustrata)
        self.n_h = np.bincount(self.psu_stratum, minlength=self.n_strata)
        self.singletons = int((self.n_h == 1).sum())
        if self.singletons and lonely == "fail":
            raise ValueError(f"{self.singletons} singleton strata; see Module 3")
        self.lonely = lonely
        self.n = len(self.w)
        # Design degrees of freedom = #PSUs - #strata (standard rule).
        self.df = int(self.n_psu - self.n_strata)

    def covariance(self, infl):
        """Taylor covariance: sum_h n_h/(n_h-1) sum_i (u_hi - ubar_h)(...)'.

        u_hi = total of the influence values in PSU i of stratum h.
        """
        infl = np.asarray(infl, float)
        if infl.ndim == 1:
            infl = infl[:, None]
        tot = np.zeros((self.n_psu, infl.shape[1]))
        np.add.at(tot, self.psu_code, infl)
        sums = np.zeros((self.n_strata, infl.shape[1]))
        np.add.at(sums, self.psu_stratum, tot)
        centres = sums / self.n_h[:, None]
        dev = tot - centres[self.psu_stratum]
        nh = self.n_h[self.psu_stratum]
        fac = np.where(nh > 1, nh / np.maximum(nh - 1, 1), 0.0)
        if self.lonely == "adjust" and self.singletons:
            # singleton PSU: deviation from the grand mean of PSU totals
            grand = tot.mean(axis=0)
            single = nh == 1
            dev[single] = tot[single] - grand
            fac = np.where(single, 1.0, fac)
        cov = dev.T @ (dev * fac[:, None])
        return (cov + cov.T) / 2

    def mean(self, y, domain=None, proportion=True):
        """Weighted domain mean with Taylor SE and t-based CI.

        Proportions get a logit-transformed CI (stays inside 0-1), as in the
        reviewed project pipeline (survey_engine.py).
        """
        y = np.asarray(y, float)
        keep = np.isfinite(y) if domain is None else (np.asarray(domain, bool) & np.isfinite(y))
        w = self.w[keep]
        est = float(np.dot(w, y[keep]) / w.sum())
        infl = np.zeros(self.n)
        infl[keep] = w * (y[keep] - est) / w.sum()
        se = float(np.sqrt(max(self.covariance(infl)[0, 0], 0)))
        t = stats.t.ppf(.975, self.df)
        if proportion and 0 < est < 1:
            lg, lse = np.log(est / (1 - est)), se / (est * (1 - est))
            lo, hi = 1 / (1 + np.exp(-(lg - t * lse))), 1 / (1 + np.exp(-(lg + t * lse)))
        else:
            lo, hi = est - t * se, est + t * se
        return dict(est=est, se=se, lo=float(lo), hi=float(hi), n=int(keep.sum()))


def nsch_lc_design(a, lonely="fail"):
    """Design for the NSCH-LC 2024 wide file (one row per child)."""
    return Design(a["FWC"], a["STRATACROSS"], a["HHID"], lonely=lonely)


# ---------------------------------------------------------------------------
# 2. Model matrices with a FROZEN coding (same columns in both groups)
# ---------------------------------------------------------------------------
def model_matrix(frame, numeric, categorical):
    """Intercept + numeric columns + dummies for categorical[c] levels[1:].

    categorical: dict name -> ordered list of levels; first level = reference.
    A row with any missing/unknown value becomes all-NaN (complete cases).
    Building the matrix ONCE on the full file guarantees identical columns in
    both language groups - a classic source of silent decomposition bugs.
    """
    out = pd.DataFrame({"Intercept": 1.0}, index=frame.index)
    bad = np.zeros(len(frame), bool)
    for c in numeric:
        out[c] = pd.to_numeric(frame[c], errors="coerce")
    for c, levels in categorical.items():
        v = frame[c]
        bad |= ~v.isin(levels).to_numpy()
        for lev in levels[1:]:
            out[f"{c}={lev}"] = (v == lev).astype(float)
    out.loc[bad, :] = np.nan
    return out.astype(float)


def levels_of(series):
    return sorted(pd.Series(series).dropna().unique().tolist())


# ---------------------------------------------------------------------------
# 3. Weighted least squares with influence functions (the LPM)
# ---------------------------------------------------------------------------
def wls(y, X, w):
    """Weighted LPM. Returns beta and per-row influence on beta.

    Influence of row i on beta = (X'WX)^{-1} x_i w_i e_i. Feeding these into
    Design.covariance gives the design-based (sandwich) variance.
    """
    XtWX = X.T @ (w[:, None] * X)
    beta = np.linalg.solve(XtWX, X.T @ (w * y))
    resid = y - X @ beta
    infl = (X * (w * resid)[:, None]) @ np.linalg.inv(XtWX)
    return beta, infl


def wlogit(y, X, w, maxit=100, tol=1e-12):
    """Weighted logistic regression by Newton-Raphson (IRLS). Returns beta,
    per-row influence on beta. Raises if it fails to converge."""
    w = w / w.mean()                      # scaling weights does not change beta
    beta = np.zeros(X.shape[1])
    for _ in range(maxit):
        mu = 1 / (1 + np.exp(-(X @ beta)))
        H = X.T @ ((w * mu * (1 - mu))[:, None] * X)
        step = np.linalg.solve(H, X.T @ (w * (y - mu)))
        beta += step
        if np.max(np.abs(step)) < tol:
            break
    else:
        raise RuntimeError("logit did not converge")
    mu = 1 / (1 + np.exp(-(X @ beta)))
    H = X.T @ ((w * mu * (1 - mu))[:, None] * X)
    infl = (X * (w * (y - mu))[:, None]) @ np.linalg.inv(H)
    return beta, infl


# ---------------------------------------------------------------------------
# 4. Twofold Oaxaca-Blinder on the LPM, with exact influence functions
# ---------------------------------------------------------------------------
def oaxaca(design, y, X, group_a, keep, blocks=None, reference="A"):
    """Twofold Oaxaca-Blinder decomposition of mean(y|A) - mean(y|B).

    group_a : boolean array, True = group A (English households here).
    keep    : boolean array of rows in the complete-case analysis domain.
    reference: 'A' -> coefficients of group A weight the covariate gap
               (the study's choice: explained = (xbar_A - xbar_B)' b_A,
               unexplained = xbar_B' (b_A - b_B)).
               'B' -> explained = (xbar_A - xbar_B)' b_B,
               unexplained = xbar_A' (b_A - b_B).
    Returns dict of point estimates and the full-frame influence matrix
    (columns aligned with 'terms'), so Taylor variances can be computed.
    """
    Xv = X.to_numpy(float) if isinstance(X, pd.DataFrame) else np.asarray(X, float)
    names = list(X.columns) if isinstance(X, pd.DataFrame) else [f"x{j}" for j in range(Xv.shape[1])]
    y = np.asarray(y, float)
    ok = keep & np.isfinite(y) & np.isfinite(Xv).all(axis=1)
    A, B = ok & group_a, ok & ~group_a
    w = design.w
    bA, iA = wls(y[A], Xv[A], w[A])
    bB, iB = wls(y[B], Xv[B], w[B])
    mA = np.average(Xv[A], axis=0, weights=w[A])
    mB = np.average(Xv[B], axis=0, weights=w[B])
    yA, yB = np.average(y[A], weights=w[A]), np.average(y[B], weights=w[B])
    diff = mA - mB
    bref = bA if reference == "A" else bB
    detail = diff * bref
    gap = yA - yB
    explained = detail.sum()
    unexplained = gap - explained
    # identity check: unexplained must equal the coefficient formula
    coef_formula = mB @ (bA - bB) if reference == "A" else mA @ (bA - bB)
    assert abs(unexplained - coef_formula) < 1e-10, "decomposition identity failed"
    # ---- influence functions (delta method) --------------------------------
    n = design.n
    dmean = np.zeros((n, Xv.shape[1]))
    dmean[A] = w[A][:, None] * (Xv[A] - mA) / w[A].sum()
    dmean[B] = -w[B][:, None] * (Xv[B] - mB) / w[B].sum()
    dbeta = np.zeros((n, Xv.shape[1]))
    if reference == "A":
        dbeta[A] = iA
    else:
        dbeta[B] = iB
    dexp = dmean * bref + dbeta * diff          # product rule
    dgap = np.zeros(n)
    dgap[A] = w[A] * (y[A] - yA) / w[A].sum()
    dgap[B] = -w[B] * (y[B] - yB) / w[B].sum()
    terms = ["gap", "explained", "unexplained"] + [f"explained:{c}" for c in names]
    est = [gap, explained, unexplained] + list(detail)
    infl = [dgap, dexp.sum(1), dgap - dexp.sum(1)] + [dexp[:, j] for j in range(len(names))]
    for bname, cols in (blocks or {}).items():
        j = [k for k, c in enumerate(names) if c in cols or any(c.startswith(p + "=") for p in cols)]
        terms.append(f"block:{bname}")
        est.append(detail[j].sum())
        infl.append(dexp[:, j].sum(1))
    return dict(terms=terms, est=np.array(est), infl=np.column_stack(infl),
                n=int(ok.sum()), nA=int(A.sum()), nB=int(B.sum()),
                bA=bA, bB=bB, mA=mA, mB=mB, yA=yA, yB=yB, names=names, ok=ok,
                # LPM diagnostic: own-group fitted values outside [0, 1]
                out01A=int(((Xv[A] @ bA < 0) | (Xv[A] @ bA > 1)).sum()),
                out01B=int(((Xv[B] @ bB < 0) | (Xv[B] @ bB > 1)).sum()))


def oaxaca_point_a(y, Xv, w, A, B, block_index):
    """Point estimates only, English (A) reference - used inside the bootstrap.

    Only the reference group's regression is needed: explained = (mA-mB)'bA and
    unexplained = gap - explained. (Fitting group B in every replicate is not
    needed and can fail when a sparse category gets zero bootstrap weight.)
    """
    bA = np.linalg.solve(Xv[A].T @ (w[A][:, None] * Xv[A]), Xv[A].T @ (w[A] * y[A]))
    mA = np.average(Xv[A], axis=0, weights=w[A])
    mB = np.average(Xv[B], axis=0, weights=w[B])
    detail = (mA - mB) * bA
    gap = np.average(y[A], weights=w[A]) - np.average(y[B], weights=w[B])
    ex = detail.sum()
    return np.array([gap, ex, gap - ex] + [detail[j].sum() for j in block_index])


def reference_variants(design, y, X, group_a, keep):
    """Point estimates under four reference-coefficient choices (Module 2).

    Returns dict variant -> dict(explained, unexplained[, interaction]).
      English (A) reference : E=(mA-mB)bA,  U=mB(bA-bB)          [study]
      Other (B) reference   : E=(mA-mB)bB,  U=mA(bA-bB)
      Pooled (Neumark/Jann 'pooled' incl. group dummy): b* from pooled fit
                              E=(mA-mB)b*,  U=mA(bA-b*)+mB(b*-bB)
      Threefold (B viewpoint, Jann 2008 default): E=(mA-mB)bB,
                              C=mB(bA-bB), I=(mA-mB)(bA-bB)
    """
    Xv = X.to_numpy(float)
    y = np.asarray(y, float)
    ok = keep & np.isfinite(y) & np.isfinite(Xv).all(axis=1)
    A, B = ok & group_a, ok & ~group_a
    w = design.w
    bA, _ = wls(y[A], Xv[A], w[A])
    bB, _ = wls(y[B], Xv[B], w[B])
    mA = np.average(Xv[A], axis=0, weights=w[A])
    mB = np.average(Xv[B], axis=0, weights=w[B])
    Xp = np.column_stack([Xv[ok], group_a[ok].astype(float)])
    bP = wls(y[ok], Xp, w[ok])[0][:-1]            # drop the group dummy
    d = mA - mB
    gap = np.average(y[A], weights=w[A]) - np.average(y[B], weights=w[B])
    return {
        "english_reference": dict(gap=gap, explained=d @ bA, unexplained=mB @ (bA - bB)),
        "other_reference": dict(gap=gap, explained=d @ bB, unexplained=mA @ (bA - bB)),
        "pooled_reference": dict(gap=gap, explained=d @ bP, unexplained=mA @ (bA - bP) + mB @ (bP - bB)),
        "threefold": dict(gap=gap, endowments=d @ bB, coefficients=mB @ (bA - bB), interaction=d @ (bA - bB)),
    }


# ---------------------------------------------------------------------------
# 5. Rubin's rules over the six NSCH income (FPL) implicates
# ---------------------------------------------------------------------------
def rubin(est_list, cov_list, df_complete):
    """Pool m completed-data estimates (vectors) and covariances.

    T = W + (1 + 1/m) B, Barnard-Rubin (1999) small-sample df, as in the
    reviewed pipeline (survey_engine.pool) and the Census 'Guide to Analysis
    with Multiply Imputed Data'.
    """
    E = np.vstack(est_list)
    m = E.shape[0]
    W = np.mean(np.stack(cov_list), axis=0)
    Bv = np.atleast_2d(np.cov(E, rowvar=False, ddof=1))
    T = W + (1 + 1 / m) * Bv
    q = E.mean(0)
    se = np.sqrt(np.maximum(np.diag(T), 0))
    frac = np.where(np.diag(T) > 0, (1 + 1 / m) * np.diag(Bv) / np.diag(T), 0)
    with np.errstate(divide="ignore"):
        df_old = np.where(frac > 0, (m - 1) / frac ** 2, np.inf)
    df_obs = (df_complete + 1) / (df_complete + 3) * df_complete * (1 - frac)
    df = 1 / (1 / df_old + 1 / df_obs)
    t = stats.t.ppf(.975, df)
    return dict(est=q, se=se, lo=q - t * se, hi=q + t * se, df=df)


# ---------------------------------------------------------------------------
# 6. Bootstrap: resample PSUs WITHIN strata (Rao & Wu 1988 rescaling)
# ---------------------------------------------------------------------------
def rao_wu_factors(design, rng):
    """One replicate's weight multipliers, one per ROW.

    In each stratum h with n_h PSUs, draw n_h - 1 PSUs with replacement; a
    PSU drawn c times gets multiplier c * n_h / (n_h - 1). Every row in a PSU
    shares its multiplier. (In the NSCH-LC each household PSU holds one child,
    so PSU and child resampling coincide; resampling within strata is what
    matters. With several rows per PSU, resampling rows would ignore clustering.)
    """
    f = np.empty(design.n_psu)
    for h in range(design.n_strata):
        ids = np.flatnonzero(design.psu_stratum == h)
        nh = len(ids)
        c = rng.multinomial(nh - 1, np.full(nh, 1 / nh))
        f[ids] = c * nh / (nh - 1)
    return f[design.psu_code]


# ---------------------------------------------------------------------------
# 7. Fairlie (2005) nonlinear decomposition, every block ordering
# ---------------------------------------------------------------------------
def fairlie(y, X, w, group_a, keep, blocks, coef="pooled"):
    """Fairlie decomposition of a binary-outcome gap using a logit model.

    Aggregate: explained = mean_A F(X b) - mean_B F(X b) (weighted), b from a
    pooled logit of both groups (one common choice; a judgement like the
    LPM reference choice) or of group A. Detailed contributions: sort-and-match each B child to an
    A child by predicted probability (weighted one-to-one matching is replaced
    here by the weighted-quantile matching described in the lab notes), then
    switch blocks from B values to A values one at a time. Because a logit is
    nonlinear, a block's contribution depends on which blocks were switched
    before it. Instead of Fairlie's randomised ordering we evaluate EVERY
    ordering (5 blocks -> 120 orders), so the result is deterministic and the
    Python and R programs agree exactly; we report the mean over orders (a
    Shapley-value average), the min-max range, and the as-listed order.
    """
    Xv = X.to_numpy(float)
    names = list(X.columns)
    y = np.asarray(y, float)
    ok = keep & np.isfinite(y) & np.isfinite(Xv).all(axis=1)
    A, B = ok & group_a, ok & ~group_a
    if coef == "pooled":
        b, _ = wlogit(y[ok], Xv[ok], w[ok])
    else:
        b, _ = wlogit(y[A], Xv[A], w[A])
    F = lambda z: 1 / (1 + np.exp(-z))
    XA, XB, wA, wB = Xv[A], Xv[B], w[A], w[B]
    pA = np.average(F(XA @ b), weights=wA)
    pB = np.average(F(XB @ b), weights=wB)
    explained = pA - pB
    gap = np.average(y[A], weights=wA) - np.average(y[B], weights=wB)
    # Weighted quantile matching: rank both groups by predicted probability
    # and pair the B child at weighted quantile q with the A child at the same
    # weighted quantile. This keeps the matched A sample representative of A.
    # Stable sort on predictions rounded to 10 decimals: children with identical
    # covariates tie exactly, and a stable sort keeps file order among ties, so
    # Python and R build the SAME matched pairs.
    oA = np.argsort(np.round(XA @ b, 10), kind="stable")
    oB = np.argsort(np.round(XB @ b, 10), kind="stable")
    cA = np.cumsum(wA[oA]) / wA.sum()
    cB = (np.cumsum(wB[oB]) - wB[oB] / 2) / wB.sum()
    match = oA[np.minimum(np.searchsorted(cA, cB), len(oA) - 1)]
    XB_sorted = XB[oB]
    XA_matched = XA[match]
    wts = wB[oB]
    bidx = {k: [j for j, c in enumerate(names) if c in cols or any(c.startswith(p + "=") for p in cols)]
            for k, cols in blocks.items()}
    import itertools
    keys = list(blocks)
    contrib = {k: [] for k in keys}
    first_order = {}
    for oi, order in enumerate(itertools.permutations(keys)):
        Z = XB_sorted.copy()
        prev = np.average(F(Z @ b), weights=wts)
        for k in order:
            Z[:, bidx[k]] = XA_matched[:, bidx[k]]
            cur = np.average(F(Z @ b), weights=wts)
            contrib[k].append(cur - prev)
            if oi == 0:
                first_order[k] = cur - prev
            prev = cur
    # note: after switching every block, the matched-A mean approximates pA
    detail = {k: dict(mean=float(np.mean(v)), min=float(np.min(v)), max=float(np.max(v)))
              for k, v in contrib.items()}
    return dict(gap=float(gap), explained=float(explained), unexplained=float(gap - explained),
                detail=detail, as_listed_order=first_order,
                sum_detail=float(sum(d["mean"] for d in detail.values())),
                n=int(ok.sum()), coef=coef, n_orders=len(contrib[keys[0]]))


def logit_oaxaca_at_means(y, X, w, group_a, keep):
    """The NAIVE logit decomposition (Module 2, interaction 3).

    Plug group means into the logistic function:
      explained*   = F(xbar_A b_A) - F(xbar_B b_A)
      unexplained* = F(xbar_B b_A) - F(xbar_B b_B)
    Their sum is F(xbar_A b_A) - F(xbar_B b_B), which is NOT the observed gap
    ybar_A - ybar_B, because the mean of F(x b) is not F(mean x b) for a
    nonlinear F (Jensen's inequality). The LPM has no such residual.
    """
    Xv = X.to_numpy(float)
    y = np.asarray(y, float)
    ok = keep & np.isfinite(y) & np.isfinite(Xv).all(axis=1)
    A, B = ok & group_a, ok & ~group_a
    bA, _ = wlogit(y[A], Xv[A], w[A])
    bB, _ = wlogit(y[B], Xv[B], w[B])
    F = lambda z: 1 / (1 + np.exp(-z))
    mA = np.average(Xv[A], axis=0, weights=w[A])
    mB = np.average(Xv[B], axis=0, weights=w[B])
    gap = np.average(y[A], weights=w[A]) - np.average(y[B], weights=w[B])
    e = F(mA @ bA) - F(mB @ bA)
    u = F(mB @ bA) - F(mB @ bB)
    # Fairlie-style aggregate with group-A coefficients restores additivity:
    eF = np.average(F(Xv[A] @ bA), weights=w[A]) - np.average(F(Xv[B] @ bA), weights=w[B])
    uF = np.average(F(Xv[B] @ bA), weights=w[B]) - np.average(F(Xv[B] @ bB), weights=w[B])
    return dict(gap=gap, naive_explained=e, naive_unexplained=u,
                naive_residual=gap - e - u,
                fairlie_explained=eF, fairlie_unexplained=uF,
                fairlie_residual=gap - eF - uF)
