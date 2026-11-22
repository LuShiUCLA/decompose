# nschlc_prepare.R - R twin of nschlc_prepare.py (same recodes, same reasons;
# see the Python file for the full commentary on Trap 1 and Trap 2).
PUF_URL <- "https://www2.census.gov/programs-surveys/nsch-lc/datasets/2024/nschlc_2024_puf_Stata.zip"

obtain <- function(dta_path) {
  if (file.exists(dta_path)) return(dta_path)
  dir.create(dirname(dta_path), showWarnings = FALSE, recursive = TRUE)
  z <- file.path(dirname(dta_path), "nschlc_2024_puf_Stata.zip")
  if (!file.exists(z)) utils::download.file(PUF_URL, z, mode = "wb")
  utils::unzip(z, files = "nschlc_2024_puf.dta", exdir = dirname(dta_path))
  dta_path
}

yesno <- function(x) ifelse(x %in% 1, 1, ifelse(x %in% 2, 0, NA_real_))
code <- function(x, map) { out <- unname(map[as.character(x)]); as.numeric(out) }

prepare <- function(dta_path) {
  raw <- haven::zap_labels(haven::read_dta(dta_path))
  raw <- as.data.frame(raw); names(raw) <- toupper(names(raw))
  stopifnot(nrow(raw) == 43536, length(unique(raw$HHID)) == 21768)
  w1 <- raw[raw$WAVE == 1, ]; w2 <- raw[raw$WAVE == 2, ]
  w1 <- w1[order(w1$HHID), ]; w2 <- w2[order(w2$HHID), ]
  stopifnot(identical(w1$HHID, w2$HHID))
  names(w1) <- paste0(names(w1), "_W1"); names(w2) <- paste0(names(w2), "_W2")
  a <- cbind(HHID = w1$HHID_W1, w1, w2)
  a$FWC <- a$FWC_W2
  st <- ifelse(a$STRATUM_W2 == "2A", "2", as.character(a$STRATUM_W2))   # S&A Statement: 2A -> 2
  a$STRATACROSS <- paste0(a$FIPSSTO_W2, "_", st)
  a$language <- c("1" = "English", "2" = "Spanish", "3" = "Other non-English")[as.character(a$HHLANGUAGE_W1)]
  a$language2 <- c("1" = "English", "2" = "Non-English", "3" = "Non-English")[as.character(a$HHLANGUAGE_W1)]
  for (s in c("_W1", "_W2")) {
    a[[paste0("ADHD_EVER", s)]] <- yesno(a[[paste0("K2Q31A", s)]])
    k <- a[[paste0("K4Q20R", s)]]
    prev <- code(k, c("1" = 0, "2" = 1, "3" = 1))
    a[[paste0("PREVENTIVE_DROPSKIP", s)]] <- prev                       # WRONG (sandbox only)
    prev[a[[paste0("S4Q01", s)]] %in% 2] <- 0                          # Trap 1: structural zero
    a[[paste0("PREVENTIVE", s)]] <- prev
    a[[paste0("INSURED", s)]] <- yesno(a[[paste0("CURRINS", s)]])         # Trap 2: use CURRINS
    a[[paste0("INSURED_CURRCOV", s)]] <- yesno(a[[paste0("CURRCOV", s)]])
    a[[paste0("USUAL_SOURCE", s)]] <- yesno(a[[paste0("K4Q01", s)]])
    a[[paste0("LOW_PERSIST", s)]] <- code(a[[paste0("K7Q84_R", s)]], c("1" = 0, "2" = 0, "3" = 1, "4" = 1))
    for (v in c("K7Q83_R", "K7Q85_R")) {
      x <- a[[paste0(v, s)]]; a[[paste0(v, s, "_C")]] <- ifelse(x %in% 1:4, x, NA_real_)
    }
  }
  for (v in c("PSCFIDGET", "PSCDAYDREAMS", "PSCDISTEASY", "PSCCONCENTRATE", "PSCMOTOR")) {
    x <- a[[paste0(v, "_W2")]]; a[[paste0(v, "_W2_C")]] <- ifelse(x %in% 1:3, x - 1, NA_real_)
  }
  a$PSCATT <- a$PSCATT_W2
  a$PSC_GE7 <- ifelse(is.na(a$PSCATT), NA_real_, as.numeric(a$PSCATT >= 7))
  a$NEW_REPORTED_ADHD <- ifelse(a$ADHD_EVER_W1 %in% 0, a$ADHD_EVER_W2, NA_real_)
  one_adult <- a$A2_RELATION_W1 %in% 8
  mh1 <- a$A1_MENTHEALTH_W1; mh2 <- a$A2_MENTHEALTH_W1
  mh <- rep(NA_real_, nrow(a))
  mh[(mh1 %in% 1:3) & ((mh2 %in% 1:3) | one_adult)] <- 0
  mh[(mh1 %in% 4:5) | (mh2 %in% 4:5)] <- 1
  a$CAREGIVER_POOR_MH <- mh
  # EARLIER rule (superseded program; reproduces the design brief's figures):
  # negative whenever caregiver 1 is observed, even if caregiver 2 is unobserved.
  a$CAREGIVER_POOR_MH_EARLIER_RULE <- ifelse((mh1 %in% 4:5) | (mh2 %in% 4:5), 1,
                                             ifelse(mh1 %in% 1:5, 0, NA_real_))
  a$AGE <- a$SC_AGE_YEARS_W2; a$AGE_BASE <- a$SC_AGE_YEARS_W1
  a$SEX <- a$SC_SEX_W1; a$RACE <- a$SC_RACE_R_W1; a$HISPANIC <- a$SC_HISPANIC_R_W1; a$EDUCATION <- a$HIGRADE_W1
  for (k in 1:6) a[[paste0("FPL", k)]] <- a[[paste0("FPL_I", k, "_W1")]] / 100
  a
}

DEMOGRAPHICS_NUM <- c("AGE", "FPL", "CAREGIVER_POOR_MH")
DEMOGRAPHICS_CAT <- c("SEX", "RACE", "HISPANIC", "EDUCATION")
CONC_FIDGET <- c("PSCCONCENTRATE_W2_C", "PSCFIDGET_W2_C")
OTHER_ATTENTION <- c("PSCMOTOR_W2_C", "PSCDAYDREAMS_W2_C", "PSCDISTEASY_W2_C")
BEHAVIOUR <- c("LOW_PERSIST_W2", "K7Q83_R_W2_C", "K7Q85_R_W2_C")
ACCESS <- c("INSURED_W2", "USUAL_SOURCE_W2", "PREVENTIVE_W2")
BLOCKS <- list(demographics = c(DEMOGRAPHICS_NUM, DEMOGRAPHICS_CAT), concentration_fidget = CONC_FIDGET,
               other_attention = OTHER_ATTENTION, persistence_homework_calm = BEHAVIOUR, access = ACCESS)
