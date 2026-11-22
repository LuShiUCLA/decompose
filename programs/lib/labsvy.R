# labsvy.R - R twin of programs/lib/labsvy.py
# ---------------------------------------------------------------------------
# Written independently from the Python toolkit so that agreement between the
# two languages is evidence, not an echo. Uses:
#   * survey (Lumley 2004, doi:10.18637/jss.v009.i08) for the design-based
#     descriptive estimates and the lonely-PSU demonstration;
#   * hand-written matrix algebra for the decomposition and its influence
#     functions, because neither survey nor the CRAN 'oaxaca' package computes
#     design-based (Taylor) variances for an Oaxaca-Blinder decomposition.
# Packages pinned in programs/R-packages.lock: survey 4.2.1, haven 2.5.4,
# jsonlite 1.8.8 (R 4.3.3).
# ---------------------------------------------------------------------------
SEED <- 20261117L
N_BOOT <- 200L

# ---- Design object (full frame, with-replacement Taylor) -------------------
make_design <- function(w, strata, psu, lonely = "fail") {
  key <- paste(strata, psu, sep = "\r")
  psu_id <- match(key, sort(unique(key)))
  ukey <- sort(unique(key))
  ustr <- sub("\r.*$", "", ukey)
  psu_stratum <- match(ustr, sort(unique(ustr)))
  n_h <- tabulate(psu_stratum, nbins = max(psu_stratum))
  singletons <- sum(n_h == 1)
  if (singletons > 0 && lonely == "fail") stop(singletons, " singleton strata (see Module 3)")
  list(w = as.numeric(w), psu_id = psu_id, psu_stratum = psu_stratum, n_h = n_h,
       n_psu = length(ukey), n_strata = length(n_h), singletons = singletons,
       lonely = lonely, df = length(ukey) - length(n_h), n = length(w))
}

# Taylor covariance from per-row influence values (matrix n x k)
taylor_cov <- function(d, infl) {
  infl <- as.matrix(infl)
  tot <- rowsum(infl, d$psu_id, reorder = TRUE)            # PSU totals, sorted id
  sums <- rowsum(tot, d$psu_stratum, reorder = TRUE)
  centres <- sums / d$n_h
  dev <- tot - centres[d$psu_stratum, , drop = FALSE]
  nh <- d$n_h[d$psu_stratum]
  fac <- ifelse(nh > 1, nh / pmax(nh - 1, 1), 0)
  if (d$lonely == "adjust" && d$singletons > 0) {
    single <- nh == 1
    grand <- colMeans(tot)
    dev[single, ] <- sweep(tot[single, , drop = FALSE], 2, grand)
    fac[single] <- 1
  }
  cv <- crossprod(dev, dev * fac)
  (cv + t(cv)) / 2
}

svy_mean <- function(d, y, domain, proportion = TRUE) {
  keep <- domain & is.finite(y)
  w <- d$w[keep]
  est <- sum(w * y[keep]) / sum(w)
  infl <- numeric(d$n)
  infl[keep] <- w * (y[keep] - est) / sum(w)
  se <- sqrt(max(taylor_cov(d, infl)[1, 1], 0))
  tq <- qt(.975, d$df)
  if (proportion && est > 0 && est < 1) {
    lg <- log(est / (1 - est)); lse <- se / (est * (1 - est))
    lo <- plogis(lg - tq * lse); hi <- plogis(lg + tq * lse)
  } else { lo <- est - tq * se; hi <- est + tq * se }
  list(est = est, se = se, lo = lo, hi = hi, n = sum(keep))
}

# ---- Model matrix with frozen coding ---------------------------------------
model_matrix <- function(df, numeric, categorical) {
  X <- matrix(1, nrow(df), 1, dimnames = list(NULL, "Intercept"))
  bad <- rep(FALSE, nrow(df))
  for (v in numeric) X <- cbind(X, setNames(data.frame(as.numeric(df[[v]])), v) |> as.matrix())
  for (v in names(categorical)) {
    lev <- categorical[[v]]
    bad <- bad | !(df[[v]] %in% lev)
    for (l in lev[-1]) {
      col <- matrix(as.numeric(df[[v]] == l), ncol = 1, dimnames = list(NULL, paste0(v, "=", l)))
      X <- cbind(X, col)
    }
  }
  X[bad, ] <- NA
  X
}

# ---- WLS with influence ----------------------------------------------------
wls <- function(y, X, w) {
  XtWX <- crossprod(X, X * w)
  beta <- solve(XtWX, crossprod(X, w * y))[, 1]
  r <- y - X %*% beta
  infl <- (X * as.numeric(w * r)) %*% solve(XtWX)
  list(beta = beta, infl = infl)
}

# weighted logit via glm (quasibinomial gives the same point estimates as a
# survey-weighted logit; we use only the coefficients here)
wlogit <- function(y, X, w) {
  f <- suppressWarnings(glm.fit(X, y, weights = w / mean(w), family = quasibinomial(),
                                control = glm.control(epsilon = 1e-12, maxit = 100)))
  if (!f$converged) stop("logit did not converge")
  f$coefficients
}

# ---- Twofold Oaxaca-Blinder (A = English reference) ------------------------
oaxaca <- function(d, y, X, groupA, keep, blocks = NULL, reference = "A") {
  ok <- keep & is.finite(y) & stats::complete.cases(X)
  A <- ok & groupA; B <- ok & !groupA
  w <- d$w
  fA <- wls(y[A], X[A, , drop = FALSE], w[A]); fB <- wls(y[B], X[B, , drop = FALSE], w[B])
  mA <- colSums(X[A, , drop = FALSE] * w[A]) / sum(w[A])
  mB <- colSums(X[B, , drop = FALSE] * w[B]) / sum(w[B])
  yA <- sum(w[A] * y[A]) / sum(w[A]); yB <- sum(w[B] * y[B]) / sum(w[B])
  diff <- mA - mB
  bref <- if (reference == "A") fA$beta else fB$beta
  detail <- diff * bref
  gap <- yA - yB; ex <- sum(detail); un <- gap - ex
  coef_formula <- if (reference == "A") sum(mB * (fA$beta - fB$beta)) else sum(mA * (fA$beta - fB$beta))
  stopifnot(abs(un - coef_formula) < 1e-10)
  p <- ncol(X)
  dmean <- matrix(0, d$n, p)
  dmean[A, ] <- sweep(X[A, , drop = FALSE], 2, mA) * w[A] / sum(w[A])
  dmean[B, ] <- -sweep(X[B, , drop = FALSE], 2, mB) * w[B] / sum(w[B])
  dbeta <- matrix(0, d$n, p)
  if (reference == "A") dbeta[A, ] <- fA$infl else dbeta[B, ] <- fB$infl
  dexp <- sweep(dmean, 2, bref, `*`) + sweep(dbeta, 2, diff, `*`)
  dgap <- numeric(d$n)
  dgap[A] <- w[A] * (y[A] - yA) / sum(w[A]); dgap[B] <- -w[B] * (y[B] - yB) / sum(w[B])
  nm <- colnames(X)
  terms <- c("gap", "explained", "unexplained", paste0("explained:", nm))
  est <- c(gap, ex, un, detail)
  infl <- cbind(dgap, rowSums(dexp), dgap - rowSums(dexp), dexp)
  for (b in names(blocks)) {
    cols <- blocks[[b]]
    j <- which(nm %in% cols | sapply(nm, function(z) any(startsWith(z, paste0(cols, "=")))))
    terms <- c(terms, paste0("block:", b))
    est <- c(est, sum(detail[j]))
    infl <- cbind(infl, rowSums(dexp[, j, drop = FALSE]))
  }
  list(terms = terms, est = est, infl = infl, n = sum(ok), nA = sum(A), nB = sum(B),
       bA = fA$beta, bB = fB$beta, mA = mA, mB = mB, yA = yA, yB = yB, names = nm, ok = ok,
       # LPM diagnostic: own-group fitted values outside [0, 1]
       out01A = sum(abs(drop(X[A, , drop = FALSE] %*% fA$beta) - 0.5) > 0.5),
       out01B = sum(abs(drop(X[B, , drop = FALSE] %*% fB$beta) - 0.5) > 0.5))
}

oaxaca_point_a <- function(y, X, w, A, B, block_index) {
  XA <- X[A, , drop = FALSE]
  bA <- solve(crossprod(XA, XA * w[A]), crossprod(XA, w[A] * y[A]))[, 1]
  mA <- colSums(XA * w[A]) / sum(w[A])
  mB <- colSums(X[B, , drop = FALSE] * w[B]) / sum(w[B])
  detail <- (mA - mB) * bA
  gap <- sum(w[A] * y[A]) / sum(w[A]) - sum(w[B] * y[B]) / sum(w[B])
  c(gap, sum(detail), gap - sum(detail), sapply(block_index, function(j) sum(detail[j])))
}

reference_variants <- function(d, y, X, groupA, keep) {
  ok <- keep & is.finite(y) & stats::complete.cases(X)
  A <- ok & groupA; B <- ok & !groupA; w <- d$w
  bA <- wls(y[A], X[A, , drop = FALSE], w[A])$beta
  bB <- wls(y[B], X[B, , drop = FALSE], w[B])$beta
  mA <- colSums(X[A, , drop = FALSE] * w[A]) / sum(w[A])
  mB <- colSums(X[B, , drop = FALSE] * w[B]) / sum(w[B])
  Xp <- cbind(X[ok, , drop = FALSE], group = as.numeric(groupA[ok]))
  bP <- wls(y[ok], Xp, w[ok])$beta[seq_len(ncol(X))]
  dd <- mA - mB
  gap <- sum(w[A] * y[A]) / sum(w[A]) - sum(w[B] * y[B]) / sum(w[B])
  list(english_reference = c(gap = gap, explained = sum(dd * bA), unexplained = sum(mB * (bA - bB))),
       other_reference = c(gap = gap, explained = sum(dd * bB), unexplained = sum(mA * (bA - bB))),
       pooled_reference = c(gap = gap, explained = sum(dd * bP), unexplained = sum(mA * (bA - bP)) + sum(mB * (bP - bB))),
       threefold = c(gap = gap, endowments = sum(dd * bB), coefficients = sum(mB * (bA - bB)), interaction = sum(dd * (bA - bB))))
}

# ---- Rubin pooling with Barnard-Rubin df -----------------------------------
rubin <- function(est_list, cov_list, df_complete) {
  E <- do.call(rbind, est_list); m <- nrow(E)
  W <- Reduce(`+`, cov_list) / m
  Bv <- stats::cov(E)
  Tm <- W + (1 + 1 / m) * Bv
  q <- colMeans(E); se <- sqrt(pmax(diag(Tm), 0))
  frac <- ifelse(diag(Tm) > 0, (1 + 1 / m) * diag(Bv) / diag(Tm), 0)
  df_old <- ifelse(frac > 0, (m - 1) / frac^2, Inf)
  df_obs <- (df_complete + 1) / (df_complete + 3) * df_complete * (1 - frac)
  df <- 1 / (1 / df_old + 1 / df_obs)
  tq <- qt(.975, df)
  list(est = q, se = se, lo = q - tq * se, hi = q + tq * se)
}

# ---- Rao-Wu PSU bootstrap multipliers --------------------------------------
rao_wu_factors <- function(d) {
  f <- numeric(d$n_psu)
  for (h in seq_len(d$n_strata)) {
    ids <- which(d$psu_stratum == h); nh <- length(ids)
    cnt <- tabulate(sample.int(nh, nh - 1, replace = TRUE), nbins = nh)
    f[ids] <- cnt * nh / (nh - 1)
  }
  f[d$psu_id]
}

# ---- Naive logit decomposition at the means vs Fairlie aggregate ----------
logit_oaxaca_at_means <- function(y, X, w, groupA, keep) {
  ok <- keep & is.finite(y) & stats::complete.cases(X)
  A <- ok & groupA; B <- ok & !groupA
  bA <- wlogit(y[A], X[A, , drop = FALSE], w[A]); bB <- wlogit(y[B], X[B, , drop = FALSE], w[B])
  mA <- colSums(X[A, , drop = FALSE] * w[A]) / sum(w[A]); mB <- colSums(X[B, , drop = FALSE] * w[B]) / sum(w[B])
  gap <- sum(w[A] * y[A]) / sum(w[A]) - sum(w[B] * y[B]) / sum(w[B])
  e <- plogis(sum(mA * bA)) - plogis(sum(mB * bA)); u <- plogis(sum(mB * bA)) - plogis(sum(mB * bB))
  wm <- function(v, ww) sum(v * ww) / sum(ww)
  eF <- wm(plogis(X[A, ] %*% bA), w[A]) - wm(plogis(X[B, ] %*% bA), w[B])
  uF <- wm(plogis(X[B, ] %*% bA), w[B]) - wm(plogis(X[B, ] %*% bB), w[B])
  c(gap = gap, naive_explained = e, naive_unexplained = u, naive_residual = gap - e - u,
    fairlie_explained = eF, fairlie_unexplained = uF, fairlie_residual = gap - eF - uF)
}

# ---- Fairlie (2005) with randomised block order ----------------------------
perms <- function(v) if (length(v) <= 1) list(v) else do.call(c, lapply(seq_along(v), function(i) lapply(perms(v[-i]), function(p) c(v[i], p))))
# Every ordering of the blocks is evaluated (deterministic; matches Python's
# itertools.permutations order exactly).
fairlie <- function(y, X, w, groupA, keep, blocks, coef = "pooled") {
  ok <- keep & is.finite(y) & stats::complete.cases(X)
  A <- ok & groupA; B <- ok & !groupA
  b <- if (coef == "pooled") wlogit(y[ok], X[ok, , drop = FALSE], w[ok]) else wlogit(y[A], X[A, , drop = FALSE], w[A])
  XA <- X[A, , drop = FALSE]; XB <- X[B, , drop = FALSE]; wA <- w[A]; wB <- w[B]
  wm <- function(v, ww) sum(v * ww) / sum(ww)
  pA <- wm(plogis(XA %*% b), wA); pB <- wm(plogis(XB %*% b), wB)
  gap <- wm(y[A], wA) - wm(y[B], wB)
  oA <- order(round(XA %*% b, 10)); oB <- order(round(XB %*% b, 10))   # stable; ties keep file order (as Python)
  cA <- cumsum(wA[oA]) / sum(wA)
  cB <- (cumsum(wB[oB]) - wB[oB] / 2) / sum(wB)
  pos <- pmin(findInterval(cB, cA, left.open = TRUE) + 1, length(oA))
  XBs <- XB[oB, , drop = FALSE]; XAm <- XA[oA[pos], , drop = FALSE]; wts <- wB[oB]
  nm <- colnames(X)
  bidx <- lapply(blocks, function(cols) which(nm %in% cols | sapply(nm, function(z) any(startsWith(z, paste0(cols, "="))))))
  contrib <- setNames(vector("list", length(blocks)), names(blocks))
  first <- list(); allp <- perms(names(blocks))
  for (r in seq_along(allp)) {
    ord <- allp[[r]]
    Z <- XBs; prev <- wm(plogis(Z %*% b), wts)
    for (k in ord) {
      Z[, bidx[[k]]] <- XAm[, bidx[[k]]]
      cur <- wm(plogis(Z %*% b), wts)
      contrib[[k]] <- c(contrib[[k]], cur - prev); if (r == 1) first[[k]] <- cur - prev; prev <- cur
    }
  }
  detail <- lapply(contrib, function(v) c(mean = mean(v), min = min(v), max = max(v)))
  list(gap = gap, explained = pA - pB, unexplained = gap - (pA - pB), detail = detail, as_listed_order = first,
       sum_detail = sum(sapply(detail, `[[`, "mean")), n = sum(ok), coef = coef, n_orders = length(allp))
}
