#!/usr/bin/env Rscript
# =============================================================================
# Decomposition Learning Lab - CORE STUDY PROGRAM (R)
# Household language and caregiver-reported ADHD diagnosis, NSCH-LC 2024.
# Independent R twin of decomposition_lab_core.py (same steps, same checks).
#
# RUN: Rscript programs/core/decomposition_lab_core.R, or source() this file,
# or paste it into the R console (it finds or downloads the lab folder itself).
# Packages (see programs/R-packages.lock): survey 4.2.1, haven 2.5.4,
# jsonlite 1.8.8; tested on R 4.3.3.
# Why no 'oaxaca' / 'srvyr' package? The CRAN 'oaxaca' package does not
# accept a survey design (no strata/PSU variance); srvyr only wraps survey.
# We use survey directly for descriptives and hand-code the decomposition.
# =============================================================================
# ---- Find the lab folder ----------------------------------------------------
# Works with Rscript, with source() / RStudio's "Source" button, and when the
# whole program is pasted into the R console. If the lab folder cannot be
# found, the program downloads it from GitHub (about 2 MB) into the current
# working directory and carries on. To use a copy you already have, put its
# path here (the folder that contains 'programs' and 'data-notes'):
LAB_FOLDER <- ""   # e.g. "C:/Users/you/Downloads/decompose-main"
LAB_ZIP_URL <- "https://github.com/LuShiUCLA/decompose/archive/refs/heads/main.zip"
find_lab_root <- function(hint) {
  is_root <- function(d) length(d) == 1 && !is.na(d) && nzchar(d) && file.exists(file.path(d, "programs", "lib", "labsvy.R"))
  cand <- hint
  a <- commandArgs(trailingOnly = FALSE); f <- sub("^--file=", "", a[grep("^--file=", a)])
  if (length(f) == 1) cand <- c(cand, file.path(dirname(f), "..", ".."))
  for (i in rev(seq_len(sys.nframe()))) {                     # source("...")
    of <- tryCatch(sys.frame(i)$ofile, error = function(e) NULL)
    if (is.character(of) && length(of) == 1) { cand <- c(cand, file.path(dirname(of), "..", "..")); break }
  }
  if (requireNamespace("rstudioapi", quietly = TRUE) && isTRUE(tryCatch(rstudioapi::isAvailable(), error = function(e) FALSE))) {
    p <- tryCatch(rstudioapi::getSourceEditorContext()$path, error = function(e) "")
    if (is.character(p) && length(p) == 1 && nzchar(p)) cand <- c(cand, file.path(dirname(p), "..", ".."))
  }
  d <- getwd(); for (i in 1:4) { cand <- c(cand, d, file.path(d, "decompose-main")); d <- dirname(d) }
  for (x in cand) if (is_root(x)) return(normalizePath(x, winslash = "/"))
  dest <- file.path(getwd(), "decompose-main")
  message("Lab folder not found. Downloading it from ", LAB_ZIP_URL, " into ", dest, " ...")
  z <- tempfile(fileext = ".zip")
  utils::download.file(LAB_ZIP_URL, z, mode = "wb", quiet = TRUE)
  utils::unzip(z, exdir = getwd())
  if (!is_root(dest)) stop("Could not set up the lab folder. Download ", LAB_ZIP_URL,
                           ", unzip it, and set LAB_FOLDER at the top of this program to the unzipped folder.")
  normalizePath(dest, winslash = "/")
}
ROOT <- find_lab_root(LAB_FOLDER)
message("Lab folder: ", ROOT)
# Install any missing package (versions used for the logged runs: programs/R-packages.lock)
for (pkg in c("survey", "haven", "jsonlite")) if (!requireNamespace(pkg, quietly = TRUE)) utils::install.packages(pkg, repos = "https://cloud.r-project.org")
source(file.path(ROOT, "programs", "lib", "labsvy.R"))
source(file.path(ROOT, "programs", "lib", "nschlc_prepare.R"))
suppressPackageStartupMessages({ library(survey); library(jsonlite) })

# >>>>>>>>>>>>>>>>>>>>>>>> EDIT THIS ONE LINE IF NEEDED <<<<<<<<<<<<<<<<<<<<<<<<
DATA_PATH <- file.path(ROOT, "data", "nschlc_2024_puf.dta")
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

OUT <- file.path(ROOT, "programs", "core", "output"); dir.create(OUT, showWarnings = FALSE)
REF <- fromJSON(file.path(ROOT, "data-notes", "reference_values.json"), simplifyVector = FALSE)
PP <- 100; TOL_PP <- 0.05; TOL_MEAN <- 0.005
LOG <- character()
say <- function(...) { s <- paste0(...); cat(s, "\n"); LOG <<- c(LOG, s) }
banner <- function(t) say("\n", strrep("=", 78), "\n", t, "\n", strrep("=", 78))
R <- list(environment = list(R = R.version.string, survey = as.character(packageVersion("survey")),
                             haven = as.character(packageVersion("haven")), seed = SEED, n_boot = N_BOOT))

# ---- STEP 0: synthetic dry run ----------------------------------------------
banner("STEP 0  Synthetic dry run (known answer)")
set.seed(SEED)
centred <- function(n) { e <- rnorm(n, 0, .1); e - mean(e) }
xA <- c(rep(1, 3600), rep(0, 2400)); xB <- c(rep(1, 800), rep(0, 3200))
yA <- 0.10 + 0.20 * xA + c(centred(3600), centred(2400))
yB <- 0.05 + 0.20 * xB + c(centred(800), centred(3200))
n <- 10000
Xs <- cbind(Intercept = 1, x = c(xA, xB))
dsyn <- make_design(rep(1, n), rep(1:50, each = n / 50), 1:n)
rs <- oaxaca(dsyn, c(yA, yB), Xs, c(rep(TRUE, 6000), rep(FALSE, 4000)), rep(TRUE, n))
ok0 <- abs(rs$est[2] - 0.08) < 1e-10 && abs(rs$est[3] - 0.05) < 1e-10
say(sprintf("gap=%.6f (true 0.13) explained=%.6f (true 0.08) unexplained=%.6f (true 0.05) -> %s",
            rs$est[1], rs$est[2], rs$est[3], if (ok0) "PASS" else "FAIL"))
if (!ok0) stop("Synthetic dry run FAILED")
R$synthetic <- list(gap = rs$est[1], explained = rs$est[2], unexplained = rs$est[3], passed = ok0)

# ---- STEP 1 -------------------------------------------------------------------
banner("STEP 1  Load the public-use file")
a <- prepare(obtain(DATA_PATH))
des <- make_design(a$FWC, a$STRATACROSS, a$HHID)
lv <- lapply(setNames(DEMOGRAPHICS_CAT, DEMOGRAPHICS_CAT), function(v) sort(unique(na.omit(a[[v]]))))
say(sprintf("children=%d strata=%d PSUs=%d design df=%d", nrow(a), des$n_strata, des$n_psu, des$df))
primary <- a$AGE >= 6 & a$AGE <= 17 & !is.na(a$language2)
primary[is.na(primary)] <- FALSE
eng <- a$language2 %in% "English"; non <- a$language2 %in% "Non-English"

# ---- STEP 2: descriptives, two ways ------------------------------------------
banner("STEP 2  Descriptives (hand Taylor) cross-checked with survey::svymean")
D <- list()
specs <- list(c("adhd", "ADHD_EVER_W2", TRUE), c("psc_mean", "PSCATT", FALSE), c("psc_ge7", "PSC_GE7", TRUE),
              c("usual", "USUAL_SOURCE_W2", TRUE), c("insured", "INSURED_W2", TRUE), c("preventive", "PREVENTIVE_W2", TRUE))
svd <- svydesign(ids = ~HHID, strata = ~STRATACROSS, weights = ~FWC, data = a, nest = TRUE)
for (s in specs) for (g in c("english", "other")) {
  prop <- as.logical(s[3]); sc <- if (prop) PP else 1
  gm <- if (g == "english") eng else non
  m <- svy_mean(des, a[[s[2]]], primary & gm, prop)
  # survey package: domain estimate from the FULL design (subset() keeps the
  # full design information - this is domain estimation, not pre-subsetting)
  sv <- svymean(as.formula(paste0("~", s[2])), subset(svd, primary & gm), na.rm = TRUE)
  D[[paste0(s[1], "_", g)]] <- list(est = m$est * sc, lo = m$lo * sc, hi = m$hi * sc, n = m$n,
                                    survey_pkg_est = coef(sv)[[1]] * sc, survey_pkg_se = SE(sv)[[1]] * sc, se = m$se * sc)
  say(sprintf("%-11s %-8s %7.2f (%.2f, %.2f) n=%d | survey pkg %.4f se %.4f vs hand se %.4f", s[1], g,
              m$est * sc, m$lo * sc, m$hi * sc, m$n, coef(sv)[[1]] * sc, SE(sv)[[1]] * sc, m$se * sc))
}
base <- a$AGE_BASE >= 6 & a$AGE_BASE <= 17
for (g in list(c("english", "English"), c("spanish", "Spanish"), c("other_language", "Other non-English"), c("nonenglish", "NE"))) {
  gm <- if (g[2] == "NE") non else (a$language %in% g[2])
  m <- svy_mean(des, a$NEW_REPORTED_ADHD, base & gm)
  D[[paste0("incident_", g[1])]] <- list(est = m$est * PP, lo = m$lo * PP, hi = m$hi * PP, n = m$n)
  say(sprintf("incident %-15s %6.2f (%.2f, %.2f) n=%d", g[1], m$est * PP, m$lo * PP, m$hi * PP, m$n))
}
# The brief's PSC scoring: sum of the five items over children with ALL five
# answered (the released PSCATT scores an unanswered item as 0).
sc <- rowSums(as.matrix(a[, paste0(c("PSCFIDGET", "PSCDAYDREAMS", "PSCDISTEASY", "PSCCONCENTRATE", "PSCMOTOR"), "_W2_C")]))
for (g in c("english", "other")) {
  gm <- if (g == "english") eng else non
  m <- svy_mean(des, sc, primary & gm, FALSE)
  D[[paste0("psc_mean_complete_items_", g)]] <- list(est = m$est, lo = m$lo, hi = m$hi, n = m$n)
  m2 <- svy_mean(des, ifelse(is.na(sc), NA_real_, as.numeric(sc >= 7)), primary & gm)
  D[[paste0("psc_ge7_complete_items_", g)]] <- list(est = m2$est * PP, lo = m2$lo * PP, hi = m2$hi * PP, n = m2$n)
  say(sprintf("PSC complete-item scoring %-8s mean %.3f; >=7 %.2f%%", g, m$est, m2$est * PP))
}
R$descriptives <- D

# ---- STEP 3: primary decomposition ------------------------------------------------
pooled_decomposition <- function(a, outcome, domain, blocks) {
  cols <- unlist(blocks); cats <- intersect(cols, DEMOGRAPHICS_CAT); num <- setdiff(cols, cats)
  g <- a$language2 %in% "English"
  est <- list(); cv <- list(); fits <- list()
  for (k in 1:6) {
    df <- a; df$FPL <- a[[paste0("FPL", k)]]
    X <- model_matrix(df, num, lv[cats])
    r <- oaxaca(des, a[[outcome]], X, g, domain, blocks)
    est[[k]] <- r$est; cv[[k]] <- taylor_cov(des, r$infl); fits[[k]] <- r
  }
  p <- length(fits[[1]]$bA)
  pr <- rubin(est, cv, des$df - (p - 1))
  out <- lapply(seq_along(fits[[1]]$terms), function(i) list(est = pr$est[i] * PP, lo = pr$lo[i] * PP, hi = pr$hi[i] * PP))
  names(out) <- fits[[1]]$terms
  list(out = out, fits = fits)
}
fmt <- function(d) sprintf("%7.2f  (%6.2f, %6.2f)", d$est, d$lo, d$hi)

banner("STEP 3  Primary decomposition: LPM, English-coefficient reference")
pd <- pooled_decomposition(a, "ADHD_EVER_W2", primary, BLOCKS)
prim <- pd$out; fits <- pd$fits
say(sprintf("n = %d (English %d, other-language %d)", fits[[1]]$n, fits[[1]]$nA, fits[[1]]$nB))
keep_terms <- c("gap", "explained", "unexplained", paste0("block:", names(BLOCKS)))
for (t in keep_terms) say(sprintf("%-34s %s", t, fmt(prim[[t]])))
say(sprintf("explained share = %.1f%%  ('explained' = compositional, NOT causal)", 100 * prim$explained$est / prim$gap$est))
R$primary <- list(n = fits[[1]]$n, terms = prim[keep_terms],
                  outside01_english = sapply(fits, `[[`, "out01A"), outside01_other = sapply(fits, `[[`, "out01B"))
say(sprintf("LPM fitted values outside [0,1], implicates 1-6: English %s; other-language %s",
            paste(R$primary$outside01_english, collapse = " "), paste(R$primary$outside01_other, collapse = " ")))

# ---- STEP 4: PSU bootstrap -----------------------------------------------------
banner("STEP 4  PSU bootstrap (Rao-Wu, PSUs within strata, 200 reps; R's RNG differs from numpy's)")
set.seed(SEED)
cols <- unlist(BLOCKS); cats <- intersect(cols, DEMOGRAPHICS_CAT); num <- setdiff(cols, cats)
Xk <- lapply(1:6, function(k) { df <- a; df$FPL <- a[[paste0("FPL", k)]]; model_matrix(df, num, lv[cats]) })
nm <- colnames(Xk[[1]])
bidx <- lapply(BLOCKS, function(cl) which(nm %in% cl | sapply(nm, function(z) any(startsWith(z, paste0(cl, "="))))))
ok <- fits[[1]]$ok; g <- eng
A <- ok & g; B <- ok & !g; y <- a$ADHD_EVER_W2
reps <- array(0, c(N_BOOT, 6, length(keep_terms)))
for (b in 1:N_BOOT) {
  w <- des$w * rao_wu_factors(des)
  for (k in 1:6) reps[b, k, ] <- oaxaca_point_a(y, Xk[[k]], w, A, B, bidx)
}
idx <- match(keep_terms, fits[[1]]$terms)
W <- colMeans(t(sapply(1:6, function(k) apply(reps[, k, ], 2, var))))
Q <- t(sapply(fits, function(f) f$est[idx]))
Tv <- W + (1 + 1 / 6) * apply(Q, 2, var)
boot <- list()
for (i in seq_along(keep_terms)) {
  e <- mean(Q[, i]); se <- sqrt(Tv[i])
  boot[[keep_terms[i]]] <- list(est = e * PP, lo = (e - 1.96 * se) * PP, hi = (e + 1.96 * se) * PP, se = se * PP)
  say(sprintf("%-34s %s  [Taylor %.2f, %.2f]", keep_terms[i], fmt(boot[[keep_terms[i]]]), prim[[keep_terms[i]]]$lo, prim[[keep_terms[i]]]$hi))
}
R$bootstrap <- boot

# ---- STEP 5: reference variants -------------------------------------------------
banner("STEP 5  Reference-coefficient variants")
V <- NULL
for (k in 1:6) {
  v <- reference_variants(des, y, Xk[[k]], g, primary)
  V <- if (is.null(V)) lapply(v, function(z) z / 6) else Map(function(p, q) p + q / 6, V, v)
}
V <- lapply(V, function(z) as.list(z * PP))
for (nme in names(V)) say(sprintf("%-20s %s", nme, paste(sprintf("%s=%6.2f", names(V[[nme]]), unlist(V[[nme]])), collapse = "  ")))
R$reference_variants <- V

# ---- STEP 6: logit vs LPM --------------------------------------------------------
banner("STEP 6  Logit vs LPM: additivity (reduced covariate set, see Python file)")
Xsm <- model_matrix(a, c("AGE", CONC_FIDGET, OTHER_ATTENTION, ACCESS), list(SEX = lv$SEX))
# reorder columns to match the Python matrix (Intercept, AGE, PSC..., access, SEX=2)
lo <- logit_oaxaca_at_means(y, Xsm, des$w, g, primary)
lp <- oaxaca(des, y, Xsm, g, primary)
logit <- as.list(lo * PP)
logit$lpm_explained <- lp$est[2] * PP; logit$lpm_unexplained <- lp$est[3] * PP
logit$lpm_residual <- (lp$est[1] - lp$est[2] - lp$est[3]) * PP; logit$n <- lp$n
for (k in names(logit)) say(sprintf("%-22s %9.4f", k, logit[[k]]))
R$logit_vs_lpm <- logit

# ---- STEP 7: sensitivity ----------------------------------------------------------
banner("STEP 7  Sensitivity decompositions")
S <- list()
no_prev <- BLOCKS; no_prev$access <- c("INSURED_W2", "USUAL_SOURCE_W2")
s1 <- pooled_decomposition(a, "ADHD_EVER_W2", primary, no_prev)
S$no_preventive_available <- c(list(n = s1$fits[[1]]$n), s1$out[c("gap", "explained", "unexplained")])
s2 <- pooled_decomposition(a, "ADHD_EVER_W2", primary & fits[[1]]$ok, no_prev)
S$no_preventive_samecase <- c(list(n = s2$fits[[1]]$n), s2$out[c("gap", "explained", "unexplained")])
tot <- list(demographics = BLOCKS$demographics, psc_total = "PSCATT", access = ACCESS)
s3 <- pooled_decomposition(a, "ADHD_EVER_W2", primary, tot)
S$total_score_6to17 <- c(list(n = s3$fits[[1]]$n), s3$out[c("gap", "explained", "unexplained")])
s4 <- pooled_decomposition(a, "ADHD_EVER_W2", !is.na(a$language2), tot)
S$total_score_allages <- c(list(n = s4$fits[[1]]$n), s4$out[c("gap", "explained", "unexplained")])
# The design brief's figures: same specification, EARLIER caregiver
# mental-health rule (see nschlc_prepare.R). Points only in R.
ae <- a; ae$CAREGIVER_POOR_MH <- ae$CAREGIVER_POOR_MH_EARLIER_RULE
s5 <- pooled_decomposition(ae, "ADHD_EVER_W2", primary, BLOCKS)
S$earlier_caregiver_mh_rule <- c(list(n = s5$fits[[1]]$n), s5$out[keep_terms])
s6 <- pooled_decomposition(ae, "ADHD_EVER_W2", primary, no_prev)
S$earlier_caregiver_mh_rule_no_preventive <- c(list(n = s6$fits[[1]]$n), s6$out[c("gap", "explained", "unexplained")])
for (k in names(S)) say(sprintf("%-40s n=%6d gap %s explained %s", k, S[[k]]$n, fmt(S[[k]]$gap), fmt(S[[k]]$explained)))
# The brief's exact method (see brief_method() in the Python twin): earlier rule,
# income = mean of the six implicates in ONE fit. Points only here; the brief's
# naive bootstrap intervals are reproduced in Python (R's RNG differs from numpy's).
brief_points <- function(blocks) {
  df <- ae; df$FPL <- rowMeans(as.matrix(ae[, paste0("FPL", 1:6)]))
  cols <- unlist(blocks); cats <- intersect(cols, DEMOGRAPHICS_CAT); num <- setdiff(cols, cats)
  r <- oaxaca(des, ae$ADHD_EVER_W2, model_matrix(df, num, lv[cats]), ae$language2 %in% "English", primary, blocks)
  c(list(n = r$n), setNames(as.list(r$est * PP), r$terms))
}
BMR <- brief_points(BLOCKS); BNR <- brief_points(no_prev)
say(sprintf("brief method (points): n=%d gap %.2f explained %.2f unexplained %.2f; no-preventive n=%d gap %.2f explained %.2f",
            BMR$n, BMR$gap, BMR$explained, BMR$unexplained, BNR$n, BNR$gap, BNR$explained))
R$sensitivity <- S; R$brief_method_points <- list(primary = BMR, no_preventive = BNR)

# ---- STEP 8: falsification ----------------------------------------------------------
banner("STEP 8  Falsification checks")
F <- list()
age617 <- a$AGE >= 6 & a$AGE <= 17
F$skip_counts_primary <- list(structural_zero_S4Q01_no = sum(age617 & a$S4Q01_W2 %in% 2),
  arbitrary_missing_K4Q20R_with_visit = sum(age617 & a$S4Q01_W2 %in% 1 & !(a$K4Q20R_W2 %in% 1:3)),
  S4Q01_missing = sum(age617 & !(a$S4Q01_W2 %in% 1:2)),
  S4Q01_missing_without_K4Q20R = sum(age617 & !(a$S4Q01_W2 %in% 1:2) & !(a$K4Q20R_W2 %in% 1:3)),
  preventive_missing_total = sum(age617 & is.na(a$PREVENTIVE_W2)))
for (g2 in c("english", "other")) {
  gm <- if (g2 == "english") eng else non
  F[[paste0("preventive_", g2)]] <- list(correct = svy_mean(des, a$PREVENTIVE_W2, primary & gm)$est * PP,
                                         dropped_skips = svy_mean(des, a$PREVENTIVE_DROPSKIP_W2, primary & gm)$est * PP)
  F[[paste0("insured_", g2)]] <- list(currins = svy_mean(des, a$INSURED_W2, primary & gm)$est * PP,
                                      currcov = svy_mean(des, a$INSURED_CURRCOV_W2, primary & gm)$est * PP)
}
both <- !is.na(a$INSURED_W2) & !is.na(a$INSURED_CURRCOV_W2)
F$currins_currcov_disagree_all <- sum(both & a$INSURED_W2 != a$INSURED_CURRCOV_W2)
F$currins_currcov_disagree_primary <- sum(both & primary & a$INSURED_W2 != a$INSURED_CURRCOV_W2)
a2 <- a; a2$PREVENTIVE_W2 <- a2$PREVENTIVE_DROPSKIP_W2
w2 <- pooled_decomposition(a2, "ADHD_EVER_W2", primary, BLOCKS)
F$decomp_dropped_skips <- list(n = w2$fits[[1]]$n, gap = w2$out$gap$est, explained = w2$out$explained$est, access = w2$out[["block:access"]]$est)
a3 <- a; a3$INSURED_W2 <- a3$INSURED_CURRCOV_W2
w3 <- pooled_decomposition(a3, "ADHD_EVER_W2", primary, BLOCKS)
F$decomp_currcov <- list(n = w3$fits[[1]]$n, explained = w3$out$explained$est, access = w3$out[["block:access"]]$est)
# Pre-subset vs domain - with the survey package's own lonely-PSU options
dom <- svymean(~ADHD_EVER_W2, subset(svd, primary & non), na.rm = TRUE)
sub <- a[primary & non, ]
res <- list(domain = list(est = coef(dom)[[1]] * PP, se = SE(dom)[[1]] * PP))
for (lp_opt in c("remove", "adjust")) {
  options(survey.lonely.psu = lp_opt)
  sd_ <- svydesign(ids = ~HHID, strata = ~STRATACROSS, weights = ~FWC, data = sub, nest = TRUE)
  m <- svymean(~ADHD_EVER_W2, sd_, na.rm = TRUE)
  res[[lp_opt]] <- list(est = coef(m)[[1]] * PP, se = SE(m)[[1]] * PP,
                        singletons = sum(table(sub$STRATACROSS) == 1), df = degf(sd_))
}
options(survey.lonely.psu = "fail")
F$subset_vs_domain <- res
F$model_n <- list(model_n = fits[[1]]$n,
                  design_matrix_n = sum(primary & stats::complete.cases(Xk[[1]])))
F$model_n$missing_outcome <- F$model_n$design_matrix_n - F$model_n$model_n
say(toJSON(F, auto_unbox = TRUE, digits = 6))
R$falsification <- F

# ---- STEP 9: self-check -----------------------------------------------------------
banner("STEP 9  SELF-CHECK against logged reference values")
checks <- list()
chk <- function(name, got, want, tol) {
  okk <- abs(got - want) <= tol
  checks[[length(checks) + 1]] <<- list(figure = name, computed = round(got, 4), reference = want, tolerance = tol, result = if (okk) "PASS" else "FAIL")
  say(sprintf("[%s] %-44s computed %9.4f reference %9.4f tol +/-%s", if (okk) "PASS" else "FAIL", name, got, want, tol))
}
PR <- REF$decompositions$primary_items_age6to17
chk("primary n", fits[[1]]$n, PR$gap$n, 0)
for (t in keep_terms) {
  chk(paste(t, "(point)"), prim[[t]]$est, PR[[t]]$est, TOL_PP)
  chk(paste(t, "(95% CI low, Taylor)"), prim[[t]]$lo, PR[[t]]$lo, TOL_PP)
  chk(paste(t, "(95% CI high, Taylor)"), prim[[t]]$hi, PR[[t]]$hi, TOL_PP)
}
for (pair in list(c("no_preventive_samecase", "samecase_no_checkup"), c("no_preventive_available", "no_checkup_available_cases"),
                  c("total_score_6to17", "total_score_age6to17"), c("total_score_allages", "total_score_allages"))) {
  ref <- REF$decompositions[[pair[2]]]
  chk(paste(pair[1], "n"), S[[pair[1]]]$n, ref$gap$n, 0)
  for (t in c("gap", "explained", "unexplained")) chk(paste(pair[1], t), S[[pair[1]]][[t]]$est, ref[[t]]$est, TOL_PP)
}
RD <- REF$descriptives
for (k in c("adhd_english", "adhd_other", "psc_ge7_english", "psc_ge7_other", "usual_english", "usual_other",
            "insured_english", "insured_other", "preventive_english", "preventive_other",
            "incident_english", "incident_spanish", "incident_other_language", "incident_nonenglish")) {
  chk(k, D[[k]]$est, RD[[k]]$est, TOL_PP); chk(paste(k, "CI low"), D[[k]]$lo, RD[[k]]$lo, TOL_PP)
  chk(paste(k, "CI high"), D[[k]]$hi, RD[[k]]$hi, TOL_PP)
}
chk("psc_mean_english", D$psc_mean_english$est, RD$psc_mean_english$est, TOL_MEAN)
chk("psc_mean_other", D$psc_mean_other$est, RD$psc_mean_other$est, TOL_MEAN)
for (k in names(D)[!grepl("^incident|complete_items", names(D))]) chk(paste("survey pkg SE =", k), D[[k]]$survey_pkg_se, D[[k]]$se, 1e-6)
for (t in c("gap", "explained", "unexplained")) {
  chk(paste("bootstrap", t, "CI low vs Taylor (MC tol)"), boot[[t]]$lo, PR[[t]]$lo, 0.5)
  chk(paste("bootstrap", t, "CI high vs Taylor (MC tol)"), boot[[t]]$hi, PR[[t]]$hi, 0.5)
}
BR <- fromJSON(file.path(ROOT, "data-notes", "brief_values.json"), simplifyVector = FALSE)
E <- S$earlier_caregiver_mh_rule
chk("brief n, earlier caregiver-MH rule", E$n, BR$primary$n, 0)
for (t in keep_terms) chk(paste0("brief ", t, " (point), earlier rule"), E[[t]]$est, BR$primary[[t]][[1]], TOL_PP)
E6 <- S$earlier_caregiver_mh_rule_no_preventive
chk("brief no-preventive n, earlier rule", E6$n, BR$no_preventive$n, 0)
for (t in c("gap", "explained")) chk(paste0("brief no-preventive ", t, " (point), earlier rule"), E6[[t]]$est, BR$no_preventive[[t]][[1]], TOL_PP)
chk("brief n, brief method", BMR$n, BR$primary$n, 0)
for (t in keep_terms) chk(paste0("brief ", t, " (point), brief method"), BMR[[t]], BR$primary[[t]][[1]], 0.005)
chk("brief no-preventive n, brief method", BNR$n, BR$no_preventive$n, 0)
for (t in c("gap", "explained")) chk(paste0("brief no-preventive ", t, " (point), brief method"), BNR[[t]], BR$no_preventive[[t]][[1]], 0.005)
chk("brief PSC mean other (complete-item scoring)", D$psc_mean_complete_items_other$est, BR$psc_mean$other, TOL_MEAN)
chk("brief S4Q01-missing count that stays missing", F$skip_counts_primary$S4Q01_missing_without_K4Q20R, BR$skip_counts$s4q01_missing, 0)
chk("identity: gap - explained - unexplained", prim$gap$est - prim$explained$est - prim$unexplained$est, 0, 1e-9)
chk("identity: sum of blocks - explained", sum(sapply(names(BLOCKS), function(b) prim[[paste0("block:", b)]]$est)) - prim$explained$est, 0, 1e-9)
R$self_check <- checks
nf <- sum(sapply(checks, `[[`, "result") == "FAIL")
say(sprintf("\nSELF-CHECK: %d PASS, %d FAIL", length(checks) - nf, nf))
writeLines(toJSON(R, auto_unbox = TRUE, digits = 10, pretty = TRUE), file.path(OUT, "core_results_R.json"))
writeLines(LOG, file.path(OUT, "core_run_log_R.txt"))
# Rscript: exit code 1 on any FAIL. Interactive (console/RStudio): keep R open.
if (!interactive()) quit(status = if (nf == 0) 0 else 1) else message(if (nf == 0) "All self-checks passed." else paste(nf, "self-check(s) FAILED: see the log above."))
