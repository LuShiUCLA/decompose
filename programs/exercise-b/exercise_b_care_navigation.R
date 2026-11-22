#!/usr/bin/env Rscript
# =============================================================================
# Decomposition Learning Lab - EXERCISE B (R twin of exercise_b_care_navigation.py)
# Household-language gap in effective care navigation among publicly insured
# CSHCN with a coordination need, pooled annual NSCH 2016-2025.
# Oaxaca-Blinder (LPM, English reference, year fixed effects) + DFL reweighting.
# See the Python file header for the full design rationale.
# RUN: Rscript programs/exercise-b/exercise_b_care_navigation.R, or source() this file,
# or paste it into the R console (it finds or downloads the lab folder itself).
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
suppressPackageStartupMessages(library(jsonlite))

# >>>>>>>>>>>>>>>>>>>>>>>> EDIT THIS ONE LINE IF NEEDED <<<<<<<<<<<<<<<<<<<<<<<<
ANNUAL_DIR <- file.path(ROOT, "data", "annual_nsch")
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
OUT <- file.path(ROOT, "programs", "exercise-b", "output"); dir.create(OUT, showWarnings = FALSE)
LOGF <- file(file.path(OUT, "exercise_b_run_log_R.txt"), open = "wt"); sink(LOGF, split = TRUE)
YEARS <- 2016:2025
PP <- 100
BLOCKS <- list(demographics = c("AGE", "SEX", "RACE4", "HISPANIC"), ses = c("FPL", "EDUCATION"),
               coverage = "PUBLIC_AND_PRIVATE", health = "FAIR_POOR_HEALTH",
               usual_source = "USUAL_SOURCE", survey_year = "YEAR")
CATS <- c("SEX", "RACE4", "HISPANIC", "EDUCATION", "YEAR")

obtain <- function(y) {
  dta <- file.path(ANNUAL_DIR, sprintf("nsch_%de_topical.dta", y))
  if (file.exists(dta)) return(dta)
  dir.create(ANNUAL_DIR, showWarnings = FALSE, recursive = TRUE)
  zn <- if (y == 2023) "nsch_2023e_topical_Stata.zip" else sprintf("nsch_%d_topical_Stata.zip", y)
  z <- file.path(ANNUAL_DIR, zn)
  if (!file.exists(z)) utils::download.file(sprintf("https://www2.census.gov/programs-surveys/nsch/datasets/%d/%s", y, zn), z, mode = "wb")
  utils::unzip(z, files = basename(dta), exdir = ANNUAL_DIR)
  dta
}
code <- function(x, map) as.numeric(unname(map[as.character(x)]))

NEED <- c("hhid", "fipsst", "stratum", "fwc", "hhlanguage", "k5q20_r", "k5q21", "k5q22", "instype", "sc_cshcn",
          "sc_age_years", "sc_sex", "sc_race_r", "sc_hispanic_r", "higrade_tvis", "k2q01", "k4q01", paste0("fpl_i", 1:6))
prepare <- function() {
  a <- do.call(rbind, lapply(YEARS, function(y) {
    d <- as.data.frame(haven::zap_labels(haven::read_dta(obtain(y))))
    names(d) <- tolower(names(d)); d <- d[, NEED]; d$YEAR <- y
    d$stratum <- as.character(d$stratum); d$fipsst <- as.integer(d$fipsst); d$hhid <- as.numeric(d$hhid)
    d
  }))
  a$W_POOL <- a$fwc / length(YEARS)
  s <- toupper(a$stratum); s[s == "2A"] <- "2"
  a$STRATA <- paste0(a$fipsst, "_", s)
  a$PSU <- format(a$hhid, scientific = FALSE, trim = TRUE)
  a$language <- code(a$hhlanguage, c("1" = 1, "2" = 0, "3" = 0))          # 1 English, 0 other
  a$language3 <- c("English", "Spanish", "Other non-English")[match(a$hhlanguage, 1:3)]
  a$CSHCN <- a$sc_cshcn %in% 1
  a$PUBLIC <- a$instype %in% c(1, 3)
  a$NEEDCOORD <- a$k5q20_r %in% 1 | a$k5q21 %in% 1
  nav <- rep(NA_real_, nrow(a))
  nav[a$k5q21 %in% 2] <- 1                        # no extra help needed: need met (K5Q22 skipped)
  nav[a$k5q21 %in% 1 & a$k5q22 %in% 1] <- 1
  nav[a$k5q21 %in% 1 & a$k5q22 %in% c(2, 3)] <- 0
  a$NAVIGATED <- ifelse(a$NEEDCOORD, nav, NA)
  a$NAVIGATED_DROPSKIP <- ifelse(a$NEEDCOORD, code(a$k5q22, c("1" = 1, "2" = 0, "3" = 0)), NA)
  a$AGE <- as.numeric(a$sc_age_years)
  a$SEX <- ifelse(a$sc_sex %in% 1:2, a$sc_sex, NA)
  a$RACE4 <- code(a$sc_race_r, c("1" = 1, "2" = 2, "4" = 4, "3" = 7, "5" = 7, "6" = 7, "7" = 7))
  a$HISPANIC <- ifelse(a$sc_hispanic_r %in% 1:2, a$sc_hispanic_r, NA)
  a$EDUCATION <- ifelse(a$higrade_tvis %in% 1:4, a$higrade_tvis, NA)
  a$PUBLIC_AND_PRIVATE <- ifelse(a$instype %in% c(1, 3), as.numeric(a$instype == 3), NA)
  a$FAIR_POOR_HEALTH <- code(a$k2q01, c("1" = 0, "2" = 0, "3" = 0, "4" = 1, "5" = 1))
  a$USUAL_SOURCE <- code(a$k4q01, c("1" = 1, "2" = 0))
  for (k in 1:6) a[[paste0("FPL", k)]] <- a[[paste0("fpl_i", k)]] / 100
  a
}

matrices <- function(a, lv) {
  cols <- unlist(BLOCKS); num <- cols[!cols %in% CATS]
  lapply(1:6, function(k) { d <- a; d$FPL <- a[[paste0("FPL", k)]]; model_matrix(d, num, lv[CATS]) })
}

dfl_point <- function(y, X, w, E, O, ok) {
  m <- ok & w > 0
  cc <- colSums(X[m, , drop = FALSE] != 0) > 0
  b <- wlogit(as.numeric(O[m]), X[m, cc, drop = FALSE], w[m])
  p <- plogis(X[, cc, drop = FALSE] %*% b)[, 1]
  A <- m & E; B <- m & O; psi <- p / (1 - p)
  yE <- sum(w[A] * y[A]) / sum(w[A]); yO <- sum(w[B] * y[B]) / sum(w[B])
  ww <- w[A] * psi[A]; yEc <- sum(ww * y[A]) / sum(ww)
  list(gap = yE - yO, explained = yE - yEc, unexplained = yEc - yO, ess = sum(ww)^2 / sum(ww^2), max_share = max(ww) / sum(ww))
}

oaxaca_pooled <- function(des, y, Xs, E, keep) {
  fits <- lapply(Xs, function(X) oaxaca(des, y, X, E, keep, BLOCKS))
  pr <- rubin(lapply(fits, `[[`, "est"), lapply(fits, function(f) taylor_cov(des, f$infl)), des$df - (length(fits[[1]]$bA) - 1))
  kt <- c("gap", "explained", "unexplained", paste0("block:", names(BLOCKS)))
  list(terms = lapply(setNames(kt, kt), function(t) { i <- match(t, fits[[1]]$terms); list(est = pr$est[i] * PP, lo = pr$lo[i] * PP, hi = pr$hi[i] * PP) }),
       fits = fits)
}

# ---- synthetic dry run (known answer: explained = 0.1, unexplained = 0) ----
set.seed(SEED)
n <- 20000
x <- c(rnorm(n, 1), rnorm(n, 0)); Es <- c(rep(TRUE, n), rep(FALSE, n))
ys <- 0.3 + 0.1 * x + rnorm(2 * n, 0, 0.05)
Xsyn <- cbind(Intercept = 1, x = x)
dsyn <- make_design(rep(1, 2 * n), rep(1:40, each = n / 20), seq_len(2 * n))
os <- oaxaca(dsyn, ys, Xsyn, Es, rep(TRUE, 2 * n))
fs <- dfl_point(ys, Xsyn, rep(1, 2 * n), Es, !Es, rep(TRUE, 2 * n))
ex_s <- os$est[match("explained", os$terms)]
syn_ok <- abs(ex_s - 0.1) < 0.01 && abs(fs$explained - 0.1) < 0.01 && abs(fs$unexplained) < 0.01
cat(sprintf("synthetic: Oaxaca explained %.4f; DFL explained %.4f; DFL unexplained %.4f -> %s\n", ex_s, fs$explained, fs$unexplained, if (syn_ok) "PASS" else "FAIL"))
if (!syn_ok) stop("Synthetic dry run failed")

# ---- real data --------------------------------------------------------------
a <- prepare()
des <- make_design(a$W_POOL, a$STRATA, a$PSU)
cat(sprintf("children=%d strata=%d PSUs=%d df=%d\n", des$n, des$n_strata, des$n_psu, des$df))
dom <- a$CSHCN & a$PUBLIC & a$NEEDCOORD & !is.na(a$language)
flow <- list("all children" = nrow(a), "CSHCN" = sum(a$CSHCN), "and publicly insured" = sum(a$CSHCN & a$PUBLIC),
             "and coordination need" = sum(a$CSHCN & a$PUBLIC & a$NEEDCOORD), "and household language known" = sum(dom),
             "and outcome known" = sum(dom & !is.na(a$NAVIGATED)))
for (k in names(flow)) cat(sprintf("  sample flow: %-32s %7d\n", k, flow[[k]]))
E <- a$language %in% 1; O <- a$language %in% 0
y <- a$NAVIGATED
D <- list()
for (g in list(c("english", "English"), c("spanish", "Spanish"), c("other_nonenglish", "Other non-English"))) {
  m <- svy_mean(des, y, dom & a$language3 %in% g[2]); D[[paste0("navigated_", g[1])]] <- list(est = m$est * PP, lo = m$lo * PP, hi = m$hi * PP, n = m$n)
}
m <- svy_mean(des, y, dom & O); D$navigated_other <- list(est = m$est * PP, lo = m$lo * PP, hi = m$hi * PP, n = m$n)
lv <- lapply(setNames(CATS, CATS), function(v) sort(unique(na.omit(a[[v]][dom]))))
Xs <- matrices(a, lv)
ox <- oaxaca_pooled(des, y, Xs, E, dom); fits <- ox$fits; ok <- fits[[1]]$ok
cat(sprintf("Oaxaca n=%d (English %d, other %d)\n", fits[[1]]$n, fits[[1]]$nA, fits[[1]]$nB))
for (t in names(ox$terms)) cat(sprintf("  %-24s %7.2f (%6.2f, %6.2f)\n", t, ox$terms[[t]]$est, ox$terms[[t]]$lo, ox$terms[[t]]$hi))

pts <- lapply(Xs, function(X) dfl_point(y, X, des$w, E, O, ok))
ess <- mean(sapply(pts, `[[`, "ess")); maxsh <- max(sapply(pts, `[[`, "max_share"))
cat(sprintf("  reweighted English effective sample size %.0f of %d; largest single-child weight share %.4f\n", ess, fits[[1]]$nA, maxsh))
set.seed(SEED)
reps <- array(0, c(N_BOOT, 6, 3))
for (bi in 1:N_BOOT) {
  wb <- des$w * rao_wu_factors(des)
  for (k in 1:6) { r <- dfl_point(y, Xs[[k]], wb, E, O, ok); reps[bi, k, ] <- c(r$gap, r$explained, r$unexplained) }
}
dfl <- list()
for (j in 1:3) {
  t <- c("gap", "explained", "unexplained")[j]; q <- sapply(pts, `[[`, t)
  se <- sqrt(mean(apply(reps[, , j], 2, var)) + (1 + 1 / 6) * var(q))
  dfl[[t]] <- list(est = mean(q) * PP, lo = (mean(q) - 1.96 * se) * PP, hi = (mean(q) + 1.96 * se) * PP)
  cat(sprintf("  DFL %-12s %7.2f (%6.2f, %6.2f)\n", t, dfl[[t]]$est, dfl[[t]]$lo, dfl[[t]]$hi))
}

sub_matrices <- function(years) { lv2 <- lv; lv2$YEAR <- lv$YEAR[lv$YEAR %in% years]; matrices(a, lv2) }
loyo <- list()
for (yr in YEARS) {
  keep <- dom & a$YEAR != yr; Xy <- sub_matrices(setdiff(YEARS, yr))
  es <- lapply(Xy, function(X) { o <- oaxaca(des, y, X, E, keep, BLOCKS); setNames(o$est, o$terms) })
  dd <- lapply(Xy, function(X) dfl_point(y, X, des$w, E, O, ok & keep))
  loyo[[as.character(yr)]] <- list(gap = mean(sapply(es, `[[`, "gap")) * PP, oaxaca_explained = mean(sapply(es, `[[`, "explained")) * PP,
                                   dfl_explained = mean(sapply(dd, `[[`, "explained")) * PP)
}
per <- list()
for (p in list(list("2016_2021_rereleased", 2016:2021), list("2022_2025", 2022:2025))) {
  o <- oaxaca_pooled(des, y, sub_matrices(p[[2]]), E, dom & a$YEAR %in% p[[2]])
  per[[p[[1]]]] <- list(n = o$fits[[1]]$n, gap = o$terms$gap, explained = o$terms$explained)
}
# weight revision: 2016-2018 with original (un-suffixed files) vs enhanced weights
ow <- do.call(rbind, lapply(2016:2018, function(y) {
  f <- file.path(ANNUAL_DIR, "original", sprintf("nsch_%d_topical.dta", y))
  if (!file.exists(f)) { dir.create(dirname(f), FALSE, TRUE)
    utils::download.file(sprintf("https://www2.census.gov/programs-surveys/nsch/datasets/%d/nsch_%d_topical.dta", y, y), f, mode = "wb") }
  d <- as.data.frame(haven::zap_labels(haven::read_dta(f, col_select = c("hhid", "fwc")))); names(d) <- tolower(names(d))
  data.frame(hhid = as.numeric(d$hhid), fwc_original = d$fwc)
}))
fo <- ow$fwc_original[match(a$hhid, ow$hhid)]
des_o <- make_design(ifelse(is.na(fo), des$w, fo / length(YEARS)), a$STRATA, a$PSU)
keep_o <- dom & a$YEAR %in% 2016:2018; Xo <- sub_matrices(2016:2018)
rev <- list()
for (nm in c("enhanced_weights", "original_weights")) {
  o <- oaxaca_pooled(if (nm == "enhanced_weights") des else des_o, y, Xo, E, keep_o)
  rev[[nm]] <- list(n = o$fits[[1]]$n, gap = o$terms$gap, explained = o$terms$explained)
}
trap <- oaxaca_pooled(des, a$NAVIGATED_DROPSKIP, Xs, E, dom)
R <- list(sample_flow = flow, descriptives = D, oaxaca = list(n = fits[[1]]$n, terms = ox$terms), dfl = c(dfl, list(ess_english_reweighted = ess, max_weight_share = maxsh)),
          falsification = list(leave_one_year_out = loyo, period_split = per, weight_revision_2016_2018 = rev, skip_trap = list(n = trap$fits[[1]]$n, gap = trap$terms$gap)))

# ---- cross-language check against the Python output -------------------------
nf <- 0
chk <- function(nm, r, p, tol = 1e-6) { d <- abs(r - p); ok <- d < tol; nf <<- nf + !ok
  cat(sprintf("[%s] %-55s |R-Python| %.2e\n", if (ok) "PASS" else "FAIL", nm, d)) }
py <- file.path(OUT, "exercise_b_results.json")
if (file.exists(py)) {
  P <- fromJSON(py, simplifyVector = FALSE)
  for (k in names(flow)) chk(paste("sample flow", k), flow[[k]], P$sample_flow[[k]], 0.5)
  chk("DFL effective sample size", ess, P$dfl$ess_english_reweighted)
  chk("DFL largest weight share", maxsh, P$dfl$max_weight_share)
  for (g in names(D)) chk(paste("descriptive", g), D[[g]]$est, P$descriptives[[g]]$est)
  chk("Oaxaca n", fits[[1]]$n, P$oaxaca$n, 0.5)
  for (t in names(ox$terms)) for (f in c("est", "lo", "hi")) chk(paste("Oaxaca", t, f), ox$terms[[t]][[f]], P$oaxaca$terms[[t]][[f]])
  for (t in c("gap", "explained", "unexplained")) chk(paste("DFL point", t), dfl[[t]]$est, P$dfl[[t]]$est)
  for (yr in names(loyo)) for (f in names(loyo[[yr]])) chk(paste("LOYO", yr, f), loyo[[yr]][[f]], P$falsification$leave_one_year_out[[yr]][[f]])
  for (p in names(per)) chk(paste("period", p, "explained"), per[[p]]$explained$est, P$falsification$period_split[[p]]$explained$est)
  for (nm in names(rev)) for (t in c("gap", "explained")) chk(paste("weight revision", nm, t), rev[[nm]][[t]]$est, P$falsification$weight_revision_2016_2018[[nm]][[t]]$est)
  chk("skip trap gap", trap$terms$gap$est, P$falsification$skip_trap$gap$est)
  cat(sprintf("[INFO] DFL bootstrap CI (R RNG) explained (%.2f, %.2f) vs Python (%.2f, %.2f): Monte Carlo difference expected\n",
              dfl$explained$lo, dfl$explained$hi, P$dfl$explained$lo, P$dfl$explained$hi))
} else cat("Python output not found; run the Python program first for the cross-check.\n")
cat(sprintf("\nCROSS-CHECK: %d FAIL\n", nf))
writeLines(toJSON(R, auto_unbox = TRUE, digits = 10, pretty = TRUE), file.path(OUT, "exercise_b_results_R.json"))
sink(); close(LOGF)
# Rscript: exit code 1 on any FAIL. Interactive (console/RStudio): keep R open.
if (!interactive()) quit(status = if (nf == 0) 0 else 1) else message(if (nf == 0) "All self-checks passed." else paste(nf, "self-check(s) FAILED: see the log above."))
