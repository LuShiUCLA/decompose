#!/usr/bin/env Rscript
# =============================================================================
# Decomposition Learning Lab - EXERCISE A (R twin of exercise_a_access_gap.py)
# Access-to-care gap by household language: LPM Oaxaca-Blinder + Fairlie.
# See the Python file header for the full design rationale.
# RUN from repo root:  Rscript programs/exercise-a/exercise_a_access_gap.R
# =============================================================================
args <- commandArgs(trailingOnly = FALSE)
this <- normalizePath(sub("^--file=", "", args[grep("^--file=", args)]))
ROOT <- normalizePath(file.path(dirname(this), "..", ".."))
source(file.path(ROOT, "programs", "lib", "labsvy.R"))
source(file.path(ROOT, "programs", "lib", "nschlc_prepare.R"))
suppressPackageStartupMessages(library(jsonlite))

# >>>>>>>>>>>>>>>>>>>>>>>> EDIT THIS ONE LINE IF NEEDED <<<<<<<<<<<<<<<<<<<<<<<<
DATA_PATH <- file.path(ROOT, "data", "nschlc_2024_puf.dta")
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
OUT <- file.path(ROOT, "programs", "exercise-a", "output"); dir.create(OUT, showWarnings = FALSE)
LOGF <- file(file.path(OUT, "exercise_a_run_log_R.txt"), open = "wt"); sink(LOGF, split = TRUE)
PP <- 100
CATS <- c("SEX", "RACE4", "HISPANIC", "EDUCATION")

add_vars <- function(a) {
  a$FAIR_POOR_HEALTH_W2 <- code(a$K2Q01_W2, c("1" = 0, "2" = 0, "3" = 0, "4" = 1, "5" = 1))
  a$SHCN_W2 <- yesno(a$SC_CSHCN_W2)
  a$RACE4 <- code(a$RACE, c("1" = 1, "2" = 2, "4" = 4, "3" = 7, "5" = 7, "7" = 7))   # sparse 3,5 -> other
  a
}
blocks_for <- function(outcome, other_access = TRUE) {
  b <- list(demographics = c("AGE", "SEX", "RACE4", "HISPANIC"), ses = c("FPL", "EDUCATION"),
            insurance = "INSURED_W2", health = c("FAIR_POOR_HEALTH_W2", "SHCN_W2"))
  if (other_access) b$other_access <- if (outcome == "PREVENTIVE_W2") "USUAL_SOURCE_W2" else "PREVENTIVE_W2"
  b
}
matrices <- function(a, blocks, lv) {
  cols <- unlist(blocks); cats <- intersect(cols, CATS); num <- setdiff(cols, cats)
  # keep the Python column order: numeric in block order, then categoricals
  num <- cols[cols %in% num]
  lapply(1:6, function(k) { d <- a; d$FPL <- a[[paste0("FPL", k)]]; model_matrix(d, num, lv[cats[order(match(cats, cols))]]) })
}

run_spec <- function(a, des, outcome, blocks, domain, lv, label, boot = TRUE) {
  g <- a$language2 %in% "English"; y <- a[[outcome]]
  Xs <- matrices(a, blocks, lv)
  fits <- lapply(Xs, function(X) oaxaca(des, y, X, g, domain, blocks))
  pr <- rubin(lapply(fits, `[[`, "est"), lapply(fits, function(f) taylor_cov(des, f$infl)), des$df - (length(fits[[1]]$bA) - 1))
  terms <- fits[[1]]$terms
  keep <- c("gap", "explained", "unexplained", paste0("block:", names(blocks)))
  lpm <- lapply(setNames(keep, keep), function(t) { i <- match(t, terms); list(est = pr$est[i] * PP, lo = pr$lo[i] * PP, hi = pr$hi[i] * PP) })
  # English logit coefficients (same reference as the LPM); pooled logit reported separately
  fr <- lapply(Xs, function(X) fairlie(y, X, des$w, g, domain, blocks, coef = "A"))
  frp <- lapply(Xs, function(X) fairlie(y, X, des$w, g, domain, blocks, coef = "pooled"))
  mn <- function(f) mean(sapply(fr, f)) * PP
  fair <- list(gap = mn(function(f) f$gap), explained = mn(function(f) f$explained), unexplained = mn(function(f) f$unexplained),
               sum_detail = mn(function(f) f$sum_detail), n_orders = fr[[1]]$n_orders,
               detail = lapply(setNames(names(blocks), names(blocks)), function(b) list(
                 mean = mn(function(f) f$detail[[b]][["mean"]]), min = mn(function(f) f$detail[[b]][["min"]]),
                 max = mn(function(f) f$detail[[b]][["max"]]), as_listed = mn(function(f) f$as_listed_order[[b]]))),
               pooled_explained = mean(sapply(frp, `[[`, "explained")) * PP)
  if (boot) {
    set.seed(SEED)
    ok <- fits[[1]]$ok; A <- ok & g; B <- ok & !g
    reps <- matrix(0, N_BOOT, 6)
    for (bi in 1:N_BOOT) {
      w <- des$w * rao_wu_factors(des)
      for (k in 1:6) {
        m <- A & w > 0; X <- Xs[[k]]
        cc <- colSums(X[m, , drop = FALSE] != 0) > 0
        b_ <- wlogit(y[m], X[m, cc, drop = FALSE], w[m])
        Fv <- plogis(X[, cc, drop = FALSE] %*% b_)[, 1]
        reps[bi, k] <- sum(Fv[A] * w[A]) / sum(w[A]) - sum(Fv[B] * w[B]) / sum(w[B])
      }
    }
    Wv <- mean(apply(reps, 2, var)); ex <- sapply(fr, `[[`, "explained")
    se <- sqrt(Wv + (1 + 1 / 6) * var(ex))
    fair$explained_lo <- (mean(ex) - 1.96 * se) * PP; fair$explained_hi <- (mean(ex) + 1.96 * se) * PP
  }
  cat(sprintf("\n--- %s: n=%d (English %d, other-language %d)\n", label, fits[[1]]$n, fits[[1]]$nA, fits[[1]]$nB))
  for (t in c("gap", "explained", "unexplained")) cat(sprintf("%-28s LPM %7.2f (%6.2f, %6.2f)  Fairlie %7.2f\n", t, lpm[[t]]$est, lpm[[t]]$lo, lpm[[t]]$hi, fair[[t]]))
  for (b in names(blocks)) { d <- fair$detail[[b]]; l <- lpm[[paste0("block:", b)]]
    cat(sprintf("%-28s LPM %7.2f (%6.2f, %6.2f)  Fairlie %7.2f [%6.2f, %6.2f]\n", paste0("block:", b), l$est, l$lo, l$hi, d$mean, d$min, d$max)) }
  cat(sprintf("Fairlie explained, POOLED logit (no group indicator; different reference) %7.2f\n", fair$pooled_explained))
  list(n = fits[[1]]$n, n_english = fits[[1]]$nA, n_other = fits[[1]]$nB, lpm = lpm, fairlie = fair, ok = fits[[1]]$ok,
       lpm_share = lpm$explained$est / lpm$gap$est, fairlie_share = fair$explained / fair$gap)
}

a <- add_vars(prepare(obtain(DATA_PATH)))
des <- make_design(a$FWC, a$STRATACROSS, a$HHID)
lv <- lapply(setNames(CATS, CATS), function(v) sort(unique(na.omit(a[[v]]))))
dom <- a$AGE >= 6 & a$AGE <= 17 & !is.na(a$language2); dom[is.na(dom)] <- FALSE
R <- list(specs = list())
for (outcome in c("PREVENTIVE_W2", "USUAL_SOURCE_W2")) {
  cat("\n==== OUTCOME", outcome, "====\n")
  sA <- run_spec(a, des, outcome, blocks_for(outcome), dom, lv, "A: all blocks"); okA <- sA$ok; sA$ok <- NULL
  R$specs[[paste0(outcome, "|A_all_blocks")]] <- sA
  sB <- run_spec(a, des, outcome, blocks_for(outcome, FALSE), dom & okA, lv, "B: no other access, same children as A"); sB$ok <- NULL
  R$specs[[paste0(outcome, "|B_no_other_access")]] <- sB
  aw <- a; aw$PREVENTIVE_W2 <- aw$PREVENTIVE_DROPSKIP_W2; aw$INSURED_W2 <- aw$INSURED_CURRCOV_W2
  sC <- run_spec(aw, des, outcome, blocks_for(outcome), dom, lv, "C: TRAPS IN", boot = FALSE); sC$ok <- NULL
  R$specs[[paste0(outcome, "|C_traps_in")]] <- sC
}
# ---- self-check independent of the Python output ----------------------------
nf <- 0
pf <- function(ok, msg) { cat(sprintf("[%s] %s\n", if (ok) "PASS" else "FAIL", msg)); nf <<- nf + !ok }
REFD <- fromJSON(file.path(ROOT, "data-notes", "reference_values.json"), simplifyVector = FALSE)$descriptives
for (outcome in c("PREVENTIVE_W2", "USUAL_SOURCE_W2")) {
  sa <- R$specs[[paste0(outcome, "|A_all_blocks")]]; sb <- R$specs[[paste0(outcome, "|B_no_other_access")]]
  bs <- sum(sapply(names(blocks_for(outcome)), function(b) sa$lpm[[paste0("block:", b)]]$est))
  pf(abs(sa$lpm$gap$est - sa$lpm$explained$est - sa$lpm$unexplained$est) < 1e-9, paste(outcome, "LPM identity"))
  pf(abs(bs - sa$lpm$explained$est) < 1e-9, paste(outcome, "LPM blocks sum to explained"))
  pf(sa$n == sb$n && abs(sa$lpm$gap$est - sb$lpm$gap$est) < 1e-9, paste(outcome, "spec B uses the same children as A"))
}
for (pr_ in list(c("PREVENTIVE_W2", "preventive"), c("USUAL_SOURCE_W2", "usual"))) for (gn in c("english", "other")) {
  gm <- if (gn == "english") a$language2 %in% "English" else a$language2 %in% "Non-English"
  got <- svy_mean(des, a[[pr_[1]]], dom & gm)$est * PP; want <- REFD[[paste0(pr_[2], "_", gn)]]$est
  pf(abs(got - want) <= 0.05, sprintf("%s_%s %.4f vs logged %.4f (tol 0.05)", pr_[2], gn, got, want))
}
mv <- R$specs[["PREVENTIVE_W2|C_traps_in"]]$lpm$gap$est - R$specs[["PREVENTIVE_W2|A_all_blocks"]]$lpm$gap$est
pf(abs(mv) > 1, sprintf("falsification: traps-in moves the preventive gap by %.2f pp", mv))
# ---- cross-language check against the Python output (if it exists) --------
py <- file.path(OUT, "exercise_a_results.json")
if (file.exists(py)) {
  P <- fromJSON(py, simplifyVector = FALSE)$specs
  for (s in names(R$specs)) {
    for (t in c("gap", "explained", "unexplained")) {
      d <- abs(R$specs[[s]]$lpm[[t]]$est - P[[s]]$lpm[[t]]$est)
      d2 <- abs(R$specs[[s]]$fairlie[[t]] - P[[s]]$fairlie[[t]]) + if (t == "explained") abs(R$specs[[s]]$fairlie$pooled_explained - P[[s]]$fairlie$pooled_explained) else 0
      ok <- d < 1e-6 && d2 < 1e-6; nf <- nf + !ok
      cat(sprintf("[%s] %s %s: |R-Python| LPM %.2e, Fairlie %.2e\n", if (ok) "PASS" else "FAIL", s, t, d, d2))
    }
    for (b in names(R$specs[[s]]$fairlie$detail)) {
      d <- abs(R$specs[[s]]$fairlie$detail[[b]]$mean - P[[s]]$fairlie$detail[[b]]$mean); ok <- d < 1e-6; nf <- nf + !ok
      cat(sprintf("[%s] %s Fairlie %s: |R-Python| %.2e\n", if (ok) "PASS" else "FAIL", s, b, d))
    }
    if (!is.null(R$specs[[s]]$fairlie$explained_lo)) {
      d <- abs(R$specs[[s]]$fairlie$explained_lo - P[[s]]$fairlie$explained_lo)
      cat(sprintf("[INFO] %s Fairlie bootstrap CI low differs by %.3f pp (different RNGs; Monte Carlo error)\n", s, d))
    }
  }
}
cat(sprintf("\nSELF-CHECK: %d FAIL\n", nf))
writeLines(toJSON(R, auto_unbox = TRUE, digits = 10, pretty = TRUE), file.path(OUT, "exercise_a_results_R.json"))
sink(); close(LOGF)
quit(status = if (nf == 0) 0 else 1)
