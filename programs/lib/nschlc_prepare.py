"""Load the NSCH-LC 2024 public-use file and build the analysis variables.

Every recode below follows the official NSCH-LC 2024 Variable List
(NSCH-LC-Variable-List.xlsx) and reproduces the reviewed project pipeline
(nsch_lc_adhd_language_gap.py, 2026-11-17) exactly. Section numbers (Section 5.x)
refer to the lab's source-of-truth page (lab/index.html#source).
"""
from __future__ import annotations

import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

PUF_URL = "https://www2.census.gov/programs-surveys/nsch-lc/datasets/2024/nschlc_2024_puf_Stata.zip"
PUF_SHA256 = "d483c989262b2ce4a36173b2e7fd63d2a3edfddaa1b7ef2372ff8abcd99799ce"  # of the .dta used for the reference run
PSC_ITEMS = ["PSCFIDGET", "PSCDAYDREAMS", "PSCDISTEASY", "PSCCONCENTRATE", "PSCMOTOR"]


def obtain(dta_path: Path) -> Path:
    """Return the .dta path, downloading + extracting the official zip if absent."""
    dta_path = Path(dta_path)
    if dta_path.exists():
        return _checksum(dta_path)
    dta_path.parent.mkdir(parents=True, exist_ok=True)
    zpath = dta_path.parent / "nschlc_2024_puf_Stata.zip"
    if not zpath.exists():
        print(f"Downloading {PUF_URL} ...")
        tmp = zpath.with_suffix(".part")
        req = urllib.request.Request(PUF_URL, headers={"User-Agent": "decomposition-learning-lab"})
        with urllib.request.urlopen(req, timeout=120) as r, open(tmp, "wb") as f:
            while chunk := r.read(1 << 20):
                f.write(chunk)
        tmp.replace(zpath)
    with zipfile.ZipFile(zpath) as z:   # extract only the documented member
        dta_path.write_bytes(z.read("nschlc_2024_puf.dta"))
    return _checksum(dta_path)


def _checksum(dta_path: Path) -> Path:
    """Warn (do not stop) if the file differs from the one used for the reference run."""
    import hashlib
    h = hashlib.sha256(dta_path.read_bytes()).hexdigest()
    if h != PUF_SHA256:
        print(f"WARNING: {dta_path.name} SHA-256 {h} differs from the reference run's {PUF_SHA256}. "
              "Census may have re-released the file; self-check differences may come from the data, not your code.")
    return dta_path


def yesno(s):
    """1=Yes -> 1, 2=No -> 0; any other code (missing, refused) stays missing."""
    return s.map({1: 1.0, 2: 0.0})


def prepare(dta_path) -> pd.DataFrame:
    """One row per child: Wave 1 (2018/2019) and Wave 2 (2024) side by side."""
    raw = pd.read_stata(dta_path, convert_categoricals=False)
    raw.columns = raw.columns.str.upper()
    # Release checks: 21,768 children x 2 waves = 43,536 rows (Methodology
    # Report p. 4: "A total of 21,768 interviews").
    if len(raw) != 43536 or raw.HHID.nunique() != 21768:
        raise ValueError("Unexpected release size - is this the 2024 NSCH-LC PUF?")
    w1 = raw[raw.WAVE == 1].set_index("HHID").sort_index()
    w2 = raw[raw.WAVE == 2].set_index("HHID").sort_index()
    a = w1.add_suffix("_W1").join(w2.add_suffix("_W2"), validate="one_to_one").reset_index()

    # ---- Survey design (Source & Accuracy Statement pp. 6-7) ---------------
    a["FWC"] = a.FWC_W2                                    # final LC weight
    # Stratum = original state x stratum flag, with "2A" collapsed into "2"
    # exactly as the S&A Statement's Stata code does. 102 distinct values.
    a["STRATACROSS"] = a.FIPSSTO_W2.astype(str) + "_" + a.STRATUM_W2.replace({"2A": "2"}).astype(str)
    # PSU = household (HHID). Each household contributed one sampled child.

    # ---- Exposure: baseline primary household language (HHLANGUAGE) -------
    a["language"] = a.HHLANGUAGE_W1.map({1: "English", 2: "Spanish", 3: "Other non-English"})
    a["language2"] = a.HHLANGUAGE_W1.map({1: "English", 2: "Non-English", 3: "Non-English"})

    for s in ("_W1", "_W2"):
        a["ADHD_EVER" + s] = yesno(a["K2Q31A" + s])
        # TRAP 1 (Section 5.4): K4Q20R (1=0 visits, 2=1 visit, 3=2+ visits) is
        # SKIPPED when S4Q01=2 ("no medical visit at all in 12 months").
        # A child with no visit necessarily had zero PREVENTIVE visits, so the
        # skip is a STRUCTURAL ZERO, not missing data. If S4Q01 is missing
        # but K4Q20R was answered (one child aged 6-17), the answer is used;
        # otherwise it stays missing: we do not know whether a visit happened.
        a["PREVENTIVE" + s] = a["K4Q20R" + s].map({1: 0., 2: 1., 3: 1.})
        a.loc[a["S4Q01" + s] == 2, "PREVENTIVE" + s] = 0.
        # The WRONG version, kept only for the falsification sandbox:
        a["PREVENTIVE_DROPSKIP" + s] = a["K4Q20R" + s].map({1: 0., 2: 1., 3: 1.})
        # TRAP 2: CURRINS is the Census-edited insurance indicator (excludes
        # Indian Health Service-only / religious health share-only coverage).
        # CURRCOV is the raw question; the Variable List labels it "(Use CURRINS)".
        a["INSURED" + s] = yesno(a["CURRINS" + s])
        a["INSURED_CURRCOV" + s] = yesno(a["CURRCOV" + s])
        a["USUAL_SOURCE" + s] = yesno(a["K4Q01" + s])
        # K7Q84_R: 1=Always ... 4=Never works to finish tasks; 3-4 = low persistence
        a["LOW_PERSIST" + s] = a["K7Q84_R" + s].map({1: 0., 2: 0., 3: 1., 4: 1.})
        a["CONCENTRATION_DIFFICULTY" + s] = yesno(a["MEMORYCOND" + s])
        for v in ("K7Q83_R", "K7Q85_R"):          # 1=Always ... 4=Never (higher = worse)
            a[v + s + "_C"] = a[v + s].where(a[v + s].isin([1, 2, 3, 4]))

    # PSC-17 attention items, Wave 2 only (1=Never, 2=Sometimes, 3=Often).
    # Rescale to 0-2 so coefficients read "per step"; this only shifts the
    # intercept and cannot change any decomposition term.
    for v in PSC_ITEMS:
        a[v + "_W2_C"] = a[v + "_W2"].where(a[v + "_W2"].isin([1, 2, 3])) - 1
    a["PSCATT"] = a.PSCATT_W2                      # released 0-10 score
    a["PSC_GE7"] = (a.PSCATT >= 7).astype(float).where(a.PSCATT.notna())
    a["NEW_REPORTED_ADHD"] = a.ADHD_EVER_W2.where(a.ADHD_EVER_W1 == 0)

    # Caregiver poor mental health: positive if any caregiver reports fair/poor
    # (4,5); negative only if every present caregiver is observed good+.
    one_adult = a.A2_RELATION_W1 == 8
    mh1, mh2 = a.A1_MENTHEALTH_W1, a.A2_MENTHEALTH_W1
    mh = pd.Series(np.nan, index=a.index)
    mh[mh1.isin([1, 2, 3]) & (mh2.isin([1, 2, 3]) | one_adult)] = 0.
    mh[mh1.isin([4, 5]) | mh2.isin([4, 5])] = 1.
    a["CAREGIVER_POOR_MH"] = mh
    # The EARLIER rule (the project's superseded program, which produced the
    # design brief's figures): negative whenever caregiver 1 is observed,
    # even if caregiver 2 exists and is unobserved. It keeps more children but
    # codes an unknown second caregiver as 'not poor'. Used only in the
    # reconciliation sensitivity run (Module 5).
    mh_old = pd.Series(np.where(mh1.isin([4, 5]) | mh2.isin([4, 5]), 1.0,
                                np.where(mh1.notna(), 0.0, np.nan)), index=a.index)
    a["CAREGIVER_POOR_MH_EARLIER_RULE"] = mh_old

    a["AGE"] = a.SC_AGE_YEARS_W2
    a["AGE_BASE"] = a.SC_AGE_YEARS_W1
    a["SEX"] = a.SC_SEX_W1
    a["RACE"] = a.SC_RACE_R_W1
    a["HISPANIC"] = a.SC_HISPANIC_R_W1
    a["EDUCATION"] = a.HIGRADE_W1
    # Six Census income implicates (FPL_I1..FPL_I6), in units of 100 % FPL.
    for k in range(1, 7):
        a[f"FPL{k}"] = a[f"FPL_I{k}_W1"] / 100.
    return a


# The study's primary decomposition specification (Section 5.2 / reviewed pipeline)
DEMOGRAPHICS_NUM = ["AGE", "FPL", "CAREGIVER_POOR_MH"]
DEMOGRAPHICS_CAT = ["SEX", "RACE", "HISPANIC", "EDUCATION"]
CONC_FIDGET = ["PSCCONCENTRATE_W2_C", "PSCFIDGET_W2_C"]
OTHER_ATTENTION = ["PSCMOTOR_W2_C", "PSCDAYDREAMS_W2_C", "PSCDISTEASY_W2_C"]
BEHAVIOUR = ["LOW_PERSIST_W2", "K7Q83_R_W2_C", "K7Q85_R_W2_C"]
ACCESS = ["INSURED_W2", "USUAL_SOURCE_W2", "PREVENTIVE_W2"]
BLOCKS = {
    "demographics": DEMOGRAPHICS_NUM + DEMOGRAPHICS_CAT,
    "concentration_fidget": CONC_FIDGET,
    "other_attention": OTHER_ATTENTION,
    "persistence_homework_calm": BEHAVIOUR,
    "access": ACCESS,
}
