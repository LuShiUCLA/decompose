/* Retrieval-practice items. Spaced through the modules; items marked
 * `recall` return to an earlier module's idea in a new form (interleaving).
 * Every option carries a diagnosis: what the choice implies and the next step.
 * Numbers are templates ({{path}}) filled from program output. */
window.QUIZ = {
  "m1-a": { q: "The study's outcome is best described as:",
    options: [
      { t: "Whether a child has ADHD, as recorded by the caregiver in the survey", fb: "That is the trap Module 1 is about. The survey records whether a caregiver reports that a provider EVER TOLD them the child has ADHD (K2Q31A). A gap in that report can come from symptoms, access, recognition, reporting, or treatment history." },
      { t: "A caregiver's report that a provider ever said the child has ADHD", correct: true, fb: "Yes: K2Q31A asks whether a provider EVER told the caregiver the child has ADD/ADHD. Keep the noun precise; it limits what any decomposition can claim." },
      { t: "A clinician's diagnosis verified from medical records", fb: "No records are linked in the public file. It is a caregiver report of having been told." },
      { t: "A positive PSC-17 attention screen", fb: "The PSC-17 attention score (PSCATT) is a separate screening measure; a screen is not a diagnosis. In the decomposition the PSC items are covariates, not the outcome." } ] },
  "m1-b": { q: "The observed gap in reported ADHD diagnosis, English minus other-language households, ages 6–17, in the decomposition sample is about:",
    options: [
      { t: "{{primary.terms.gap.est}} percentage points", correct: true, fb: "Right: {{primary.mean_english}}% vs {{primary.mean_other}}% on the {{primary.n:0}} complete cases. Percentage points, not percent: a 9.8-point gap on a 16% base is a ~60% relative difference." },
      { t: "{{primary.terms.gap.est}} percent", fb: "Careful with units: it is a difference of two percentages, so it is in percentage points (pp). Mixing pp and % is one of the commonest reporting errors." },
      { t: "{{primary.terms.explained.est}} percentage points", fb: "That is the EXPLAINED part, not the gap. The gap is the total to be split." },
      { t: "{{desc.adhd_english.est}} percentage points", fb: "That is the English group's rate itself, not the difference between groups." } ] },
  "m2-a": { q: "In the study's twofold decomposition, each explained term equals:",
    options: [
      { t: "(English mean of the covariate − other-language mean) × English coefficient", correct: true, fb: "Yes. With English coefficients as the reference, explained = Σ (x̄_E − x̄_O)·b_E. You computed two of these by hand in the worked examples." },
      { t: "(English coefficient − other-language coefficient) × other-language mean of the covariate", fb: "That is the UNEXPLAINED (coefficient) part: x̄_O·(b_E − b_O). Re-read the worked example: explained terms move covariate means, holding slopes at the reference." },
      { t: "The coefficient on a language indicator in one pooled regression of both groups", fb: "A pooled dummy coefficient is a single adjusted difference; it does not split the gap into parts. Under the pooled-with-dummy reference it relates to the unexplained part, not the explained one." },
      { t: "The share of children with that covariate", fb: "A share alone says nothing about how the covariate relates to the outcome. You need the difference in means AND the reference slope." } ] },
  "m2-b": { recall: "Module 1", q: "Explained = {{primary.terms.explained.est}} pp. A colleague writes 'attention symptoms cause most of the language gap.' What is wrong?",
    options: [
      { t: "Nothing; the attention blocks are the largest explained parts, so attention is the main driver of the gap", fb: "They are the largest parts, but 'explained' means the gap would shrink by that much if the other-language group had the English group's distribution of those reported items, under the English slopes. That is an accounting of composition, not evidence that the items cause diagnosis differences. Caregiver-reported items may also differ by language because of reporting or measurement." },
      { t: "'Explained' is compositional, not causal, and the items are themselves caregiver reports", correct: true, fb: "Exactly. Two separate reasons: decomposition is descriptive accounting, and the covariates are reports, not objective symptoms. Measurement invariance of the PSC-17 across languages is not established in this cohort." },
      { t: "The interval for the explained part includes zero, so no conclusion about attention is possible", fb: "It does not: {{ci:primary.terms.explained}}. The problem is interpretation, not significance." },
      { t: "The decomposition should have used a logit", fb: "A logit would not make the result causal; it would also break additivity on the probability scale (Interaction 3)." } ] },
  "m2-c": { q: "If you switch from English to other-language coefficients, the gap of {{primary.terms.gap.est}} pp:",
    options: [
      { t: "Stays the same; only the split between explained and unexplained moves, because the gap is the difference in observed means", correct: true, fb: "Yes. The gap is observed; the reference only changes how it is attributed: explained {{variants.english_reference.explained}} vs {{variants.other_reference.explained}} pp. That is why the reference is a judgement you must justify." },
      { t: "Shrinks, because the other-language slopes are flatter and absorb part of the difference", fb: "The gap is the difference in observed means; no coefficient choice can change it. Try the switcher." },
      { t: "Becomes negative, because the reference group is now the lower-rate group", fb: "The observed difference in means does not depend on any model." },
      { t: "Cannot be computed", fb: "It can: it is the difference in weighted group means." } ] },
  "m3-a": { q: "Why does the lab compute the other-language rate on the FULL design (domain estimation) rather than on a file containing only other-language children?",
    options: [
      { t: "The variance formula needs every PSU in every stratum, including those with no domain member", correct: true, fb: "Right. Pre-subsetting drops PSUs and here leaves {{fals.subset_vs_domain.remove.singletons:0}} singleton strata and df {{fals.subset_vs_domain.remove.df:0}} instead of {{fals.subset_vs_domain.domain.df:0}}. In this file the SE change is small; in general it need not be." },
      { t: "Because the point estimate of the rate changes when the file is cut down to one group first", fb: "The point estimate is identical ({{fals.subset_vs_domain.domain.est}}% both ways). Only the variance machinery differs." },
      { t: "Because the survey weights are rescaled when a subset file is saved, so the rate would be biased", fb: "The weights are the same numbers; what changes is the set of PSUs the variance formula sees." },
      { t: "It does not matter at all", fb: "It changes the design: singleton strata appear and the df falls from 21,666 to {{fals.subset_vs_domain.remove.df:0}}. Software then needs an arbitrary rule (drop or 'adjust')." } ] },
  "m3-b": { q: "The bootstrap in this lab resamples:",
    options: [
      { t: "Households (PSUs) within each stratum, with Rao–Wu weight rescaling", correct: true, fb: "Yes. Resampling the units that were actually sampled keeps the design: resamples are drawn within each stratum. In this file each household contributed one child, so households and children coincide and the stratification is what matters. 200 replicates, seed 20261117." },
      { t: "Individual children across the whole file, ignoring strata, then reweighting each replicate", fb: "That treats the sample as simple random and can misstate the SE. Here each household contributed one child, so the clustering issue is minimal, but ignoring strata is still wrong in general." },
      { t: "The six income implicates", fb: "Implicates are combined with Rubin's rules (between-imputation variance), not by bootstrap." },
      { t: "Covariates, by dropping one block at a time and re-fitting the model", fb: "Bootstrap resamples sampling units, never variables." } ] },
  "m3-c": { recall: "Module 2", q: "The bootstrap 95% CI for the explained part is {{ci:boot.explained}}; the Taylor CI is {{ci:primary.terms.explained}}. What do you conclude?",
    options: [
      { t: "One of the two programs has a bug, because two correct methods should give identical limits", fb: "Not necessarily: they are different variance estimators, and the bootstrap carries Monte Carlo error with 200 replicates. Point estimates are identical; that is the check that must be exact." },
      { t: "Two variance methods agree within Monte Carlo and method error; the point estimate is identical by construction, so nothing here signals an error", correct: true, fb: "Right. Agreement within a few tenths of a pp is expected. A large disagreement would be the signal to investigate." },
      { t: "The bootstrap is always better than Taylor, so only the bootstrap interval should be reported", fb: "Neither is always better. The Census Source and Accuracy Statement documents Taylor series; the bootstrap here is a cross-check." },
      { t: "The explained part is not significant", fb: "Both intervals exclude zero." } ] },
  "m4-find1": { q: "Read the two codebook rows above. Which column tells you that some children were never asked the preventive-visit question, and why?",
    options: [
      { t: "Universe: K4Q20R is skipped when S4Q01 = 2 (no health care visit at all)", correct: true, fb: "Yes. A skip is not missing information: the answer is implied by S4Q01. The next screen asks what value it implies." },
      { t: "Values: K4Q20R has a '0 visits' category, so every child has an answer and nobody is skipped", fb: "The '0 visits' category exists for children who had some visit but no preventive one. Read the Universe column: who is asked at all?" },
      { t: "Description: 'How Many Times' implies that only children who had visits are counted in this item", fb: "The Description is a label. Routing (who is asked) is in the Universe column." },
      { t: "None: every child in the survey answers every question", fb: "Survey instruments route respondents. Read the Universe column of K4Q20R." } ] },
  "m4-find2": { q: "Read the insurance rows above. Which variable should an analysis of current insurance use, and what is the evidence in the codebook?",
    options: [
      { t: "CURRINS: the CURRCOV description itself says '(Use CURRINS)'", correct: true, fb: "Yes. The raw question (CURRCOV) and the edited indicator (CURRINS) are both on the file; the Variable List tells you which one to use." },
      { t: "CURRCOV: it is the question the caregiver actually answered, so it is closer to the truth", fb: "It is the raw answer, but the Variable List labels it '(Use CURRINS)'. Read the Description column." },
      { t: "Either: they are the same variable with different names", fb: "Their value labels differ: CURRINS does not count Indian Health Service-only or religious health-share-only coverage as insurance." },
      { t: "Neither: current insurance must be rebuilt from the separate insurance-type items", fb: "Not needed: the Census Bureau provides the edited indicator, and the codebook points to it." } ] },
  "m4-a": { q: "K4Q20R's Universe column says 'Skip if S4Q01 = 2'. For a child with S4Q01 = 2 (no medical visit in 12 months), the preventive-visit indicator should be:",
    options: [
      { t: "0: a child with no medical visit at all had no preventive visit either, so the skip is a structural zero, not missing data", correct: true, fb: "Yes. {{fals.skip_counts_primary.structural_zero_S4Q01_no:0}} children aged 6–17 are in this situation. Only {{fals.skip_counts_primary.preventive_missing_total:0}} stay missing: {{fals.skip_counts_primary.arbitrary_missing_K4Q20R_with_visit:0}} who had a visit but no K4Q20R answer, and {{fals.skip_counts_primary.S4Q01_missing_without_K4Q20R:0}} whose S4Q01 is itself missing and who gave no K4Q20R answer (one more S4Q01-missing child answered K4Q20R, and that answer is used)." },
      { t: "Missing, because the question was not asked and skipped answers should never be guessed", fb: "That is the trap. Dropping these children conditions on having had a visit, so the rate jumps to {{fals.preventive_other.dropped_skips}}% in other-language households (correct: {{fals.preventive_other.correct}}%)." },
      { t: "1, because they are healthy", fb: "Health is not the question; whether a preventive visit occurred is. With no visit at all, it did not." },
      { t: "Imputed from similar children who did answer K4Q20R, using the six FPL implicates", fb: "No imputation is needed: the answer is logically determined by S4Q01." } ] },
  "m4-b": { recall: "Module 3", q: "You run the decomposition with CURRCOV instead of CURRINS and the explained part changes only in the fourth decimal ({{fals.decomp_currcov.explained:4}} vs {{primary.terms.explained.est:4}}). What is the right conclusion?",
    options: [
      { t: "The variable choice does not matter here, so either variable is fine to report as the primary analysis", fb: "It barely matters for THIS outcome, but the insured rates differ ({{fals.insured_english.currcov}}% vs {{fals.insured_english.currins}}% in English households) and {{fals.currins_currcov_disagree_primary:0}} children disagree. Use the documented variable; check the effect, don't assume it." },
      { t: "Use CURRINS, as the Variable List says, and report the result as insensitive", correct: true, fb: "Yes: follow the codebook, then show the sensitivity. A falsification check that MOVES the insured rate also proves your code reads the variable you think it does." },
      { t: "Your program has a bug because nothing changed", fb: "Something did change (the insured rates and {{fals.currins_currcov_disagree_primary:0}} children), just not much in the decomposition. A check that moves nothing at all would be the warning sign." },
      { t: "Average the two variables", fb: "No: one is the official edited indicator; averaging mixes a known error into the estimate." } ] },
  "m5-a": { q: "The unexplained part is {{ci:primary.terms.unexplained}} pp. Which statement is defensible?",
    options: [
      { t: "There is no under-diagnosis in other-language households, because the covariates explain most of the gap", fb: "A CI including zero is not evidence of absence. It is also compatible with an unexplained gap of up to {{primary.terms.unexplained.hi}} pp, and the explained part itself depends on caregiver-reported items that may reflect under-recognition." },
      { t: "The remaining {{primary.terms.unexplained.est}} pp is imprecise and cannot say why it exists", correct: true, fb: "Yes. That is the honest reading: descriptive, quantified, with the uncertainty and the alternative explanations named." },
      { t: "Discrimination in diagnosis explains the remaining {{primary.terms.unexplained.est}} pp of the gap", fb: "The unexplained part is a residual: it absorbs omitted variables, measurement differences and the choice of reference. It is not a measure of discrimination or bias." },
      { t: "The unexplained part proves the PSC-17 is biased", fb: "Nothing in a decomposition tests measurement invariance; that needs a different design." } ] },
  "m5-b": { recall: "Module 4", q: "Which sensitivity analysis best tests whether the preventive-visit coding drives the result?",
    options: [
      { t: "Drop the preventive-visit covariate and re-run on the SAME children", correct: true, fb: "Yes: same-case explained {{sens.no_preventive_samecase.explained.est}} pp vs {{primary.terms.explained.est}} pp. Holding the sample fixed isolates the covariate's role; the available-case version (n = {{sens.no_preventive_available.n:0}}) changes the sample too." },
      { t: "Drop the K4Q20R skips and re-run, so that only children with a known visit count are analysed", fb: "That re-introduces Trap 1; it tests a known error, not a defensible alternative." },
      { t: "Switch to a logit, because a binary covariate cannot enter a linear model correctly", fb: "That changes the scale and additivity, not the coding question." },
      { t: "Use all ages", fb: "That changes the population and the covariates (behaviour items are school-age), so differences cannot be attributed to the preventive-visit coding." } ] },
  "m5-c": { recall: "Module 2", q: "The E-value for the adjusted risk ratio of new reports in Spanish- vs English-language households is {{ref.evalues.language=Spanish.e_value}} (CI limit {{ref.evalues.language=Spanish.e_value_ci}}). It means:",
    options: [
      { t: "How strong unmeasured confounding would have to be to explain away the estimate", correct: true, fb: "Yes (VanderWeele & Ding 2017). The CI E-value uses the limit closest to the null (the upper limit for a protective RR). E-values concern confounding of that risk ratio, not measurement or selection bias." },
      { t: "That the decomposition's explained part is robust to every omitted covariate", fb: "The E-value belongs to the separate longitudinal risk-ratio model, not to the decomposition." },
      { t: "The effect is causal", fb: "An E-value quantifies how strong confounding would have to be; it does not establish causation." },
      { t: "That a Spanish-language household is {{ref.evalues.language=Spanish.e_value}} times less likely to be diagnosed", fb: "The RR is {{ref.evalues.language=Spanish.rr}} (lower risk of new reports). The E-value is a sensitivity bound, not an effect size." } ] },
  "exa-1": { q: "Predict before you look: the outcome is binary and fairly common (most children had a preventive visit). With the SAME (English) reference coefficients, will the LPM and the Fairlie logit decomposition give the same explained part?",
    options: [
      { t: "Exactly the same: they decompose the same gap", fb: "Same gap, different model. The LPM weights mean differences by English slopes on the probability scale; Fairlie averages English-logit predicted probabilities. Preventive visits: LPM {{exA.specs.PREVENTIVE_W2|A_all_blocks.lpm.explained.est}} pp, Fairlie {{exA.specs.PREVENTIVE_W2|A_all_blocks.fairlie.explained}} pp." },
      { t: "Similar in sign and order of magnitude, but not identical", correct: true, fb: "Yes. Usual source: LPM {{exA.specs.USUAL_SOURCE_W2|A_all_blocks.lpm.explained.est}} pp, Fairlie {{exA.specs.USUAL_SOURCE_W2|A_all_blocks.fairlie.explained}} pp. Preventive visits: LPM {{exA.specs.PREVENTIVE_W2|A_all_blocks.lpm.explained.est}} pp, Fairlie {{exA.specs.PREVENTIVE_W2|A_all_blocks.fairlie.explained}} pp. Now look at the pooled-logit column ({{exA.specs.USUAL_SOURCE_W2|A_all_blocks.fairlie.pooled_explained}} pp for usual source): changing the reference moves the answer far more than changing the model." },
      { t: "Fairlie is always larger, because the logit curve stretches differences near the middle", fb: "In these data it is larger for both outcomes ({{exA.specs.PREVENTIVE_W2|A_all_blocks.fairlie.explained}} vs {{exA.specs.PREVENTIVE_W2|A_all_blocks.lpm.explained.est}} pp; {{exA.specs.USUAL_SOURCE_W2|A_all_blocks.fairlie.explained}} vs {{exA.specs.USUAL_SOURCE_W2|A_all_blocks.lpm.explained.est}} pp), but nothing guarantees that: it depends on where the children sit on the logit curve." },
      { t: "The logit cannot be decomposed", fb: "It can: Fairlie (2005) decomposes the gap in average predicted probabilities. What a logit loses is exact additivity of the block contributions, which is why the lab reports every ordering." } ] },
  "exa-2": { q: "Specification A puts the OTHER access outcome on the right-hand side. Why is that a problem, and what does specification B show?",
    options: [
      { t: "It is circular: access 'explains' access; specification B removes it on the same children", correct: true, fb: "Yes. A usual source of care and a preventive visit are two faces of the same access. Including one to explain the other inflates the 'explained' share. Report B as primary or both, and say why." },
      { t: "It is fine: more covariates always give a more complete decomposition, so A should be primary", fb: "More covariates raise the explained share mechanically when one of them is a near-copy of the outcome. That is not better accounting." },
      { t: "It causes multicollinearity, which biases the gap and makes specification B the only valid one", fb: "The gap is the difference in observed means; no covariate choice changes it in the same sample." } ] },
  "exa-3": { recall: "Module 4", q: "Specification C re-introduces both traps (skips dropped, CURRCOV). What happens to the preventive-visit gap?",
    options: [
      { t: "It reverses sign, {{ci:exA.specs.PREVENTIVE_W2|C_traps_in.lpm.gap}} pp: the dropped children had no visit at all, and they are more often in other-language households", correct: true, fb: "Yes. The skip trap alone turns a gap of {{exA.specs.PREVENTIVE_W2|A_all_blocks.lpm.gap.est}} pp into one favouring other-language households. A falsification run that moves this much proves your code reads S4Q01." },
      { t: "It barely changes, like the CURRCOV check in Module 4, because both traps affect few children", fb: "CURRCOV alone moves little; the skip rule moves a lot. Look at the gap in row C." },
      { t: "It doubles, because the children who are dropped are mostly in English-language households", fb: "Look at the sign of row C's gap: {{exA.specs.PREVENTIVE_W2|C_traps_in.lpm.gap.est}} pp." } ] },
  "exa-4": { recall: "Module 2", q: "In the Fairlie block table, demographics contributes between {{exA.specs.PREVENTIVE_W2|A_all_blocks.fairlie.detail.demographics.min}} and {{exA.specs.PREVENTIVE_W2|A_all_blocks.fairlie.detail.demographics.max}} pp depending on block order. How should you report it?",
    options: [
      { t: "Report one ordering and do not mention the others", fb: "That hides an arbitrary choice: Fairlie's detailed contributions depend on the order in which blocks are switched (Fairlie, 2005), as the range in the table shows." },
      { t: "Report the mean over orderings with its range, and say the aggregate is order-free", correct: true, fb: "Yes. The lab averages over all {{exA.specs.PREVENTIVE_W2|A_all_blocks.fairlie.n_orders:0}} orderings and shows the range. The LPM has no ordering problem, but it has the reference-coefficient choice instead (Module 2)." },
      { t: "Use whichever ordering gives the largest insurance share, since that is the policy-relevant block", fb: "Choosing the ordering by its result is specification searching." } ] },
  "seminar-1": { q: "Seminar question 1 (adversarial): 'Your covariates include attention items that partly MEASURE ADHD. Isn't explaining diagnosis with symptoms circular?'",
    options: [
      { t: "Yes, so the result is meaningless and the attention items should simply be dropped from the model", fb: "Too strong. The question the decomposition answers is precisely whether the gap tracks reported symptom composition. The defence is to show what happens without them." },
      { t: "Partly; that is why the blocks are reported separately, with a total-score version", correct: true, fb: "Good defence: name the circularity, show it in the blocks ({{primary.terms.block:concentration_fidget.est}} and {{primary.terms.block:other_attention.est}} pp), and point to the sensitivity specification (total score: explained {{sens.total_score_6to17.explained.est}} pp)." },
      { t: "No, symptoms and diagnosis are unrelated, so including the items cannot be circular", fb: "They are strongly related; that relation is exactly what the reference coefficients estimate." } ] },
  "seminar-2": { q: "Seminar question 2: 'Why should I believe English coefficients are the right reference?'",
    options: [
      { t: "Because it is the default in the software, and reviewers expect the default reference", fb: "Defaults are not justifications. Reviewers will ask exactly this." },
      { t: "It asks a specific counterfactual, and the pooled and other-language references are shown too", correct: true, fb: "Yes: justify, then show sensitivity: explained {{variants.english_reference.explained}} (English), {{variants.pooled_reference.explained}} (pooled), {{variants.other_reference.explained}} pp (other-language)." },
      { t: "Because the other-language coefficients are not significant, so they cannot be used as a reference", fb: "Choosing a reference by significance is specification searching." } ] },
  "exb-1": { q: "Predict before you look: among publicly insured children with special health care needs who needed care coordination, how will effective navigation compare between English-language and other-language households?",
    options: [
      { t: "Much lower in other-language households (a gap of 10 pp or more)", fb: "A reasonable expectation, given the access gaps in Exercise A, but not what these data show: English {{exB.descriptives.navigated_english.est}}% vs other-language {{exB.descriptives.navigated_other.est}}%. Hold on to the surprise; it is the point of the exercise." },
      { t: "Somewhat lower in other-language households", fb: "Not in these data: English {{exB.descriptives.navigated_english.est}}% vs other-language {{exB.descriptives.navigated_other.est}}%, and the interval for the difference includes zero." },
      { t: "About the same, with an interval that includes zero", correct: true, fb: "Yes: English {{exB.descriptives.navigated_english.est}}% vs other-language {{exB.descriptives.navigated_other.est}}%; gap {{ci:exB.oaxaca.terms.gap}} pp. Next question: what can a decomposition of a gap this uncertain tell you?" },
      { t: "It cannot be estimated from public data", fb: "It can, by pooling ten annual NSCH files; the 2024 NSCH-LC follow-up did not ask the coordination items." } ] },
  "exb-2": { q: "The DFL reweighting gives an effective sample size of {{exB.dfl.ess_english_reweighted:0}} for the reweighted English-language group (of {{exB.oaxaca.n_english:0}}). What does that tell you?",
    options: [
      { t: "Few English-language children resemble the other-language group", correct: true, fb: "Yes. Reweighting can only borrow from children who exist: with poor overlap a few large weights dominate (the largest single child carries {{exB.dfl_max_weight_pct:1}}% of the weight). That is why DFL's interval ({{ci:exB.dfl.explained}}) is wider than Oaxaca's ({{ci:exB.oaxaca.terms.explained}})." },
      { t: "The bootstrap failed to converge, so the effective sample size is not interpretable", fb: "The bootstrap ran; the effective sample size is a property of the weights, not of the variance method." },
      { t: "DFL is biased, so use Oaxaca only", fb: "Oaxaca does not escape the problem: it extrapolates the English regression line into regions with few English children. DFL makes the thin overlap visible; that is useful." },
      { t: "Nothing: the effective sample size only changes the n reported in the methods section", fb: "It sets how much information the counterfactual mean carries, so it matters for precision and for how far you can trust the explained part." } ] },
  "exb-3": { recall: "Module 4", q: "K5Q22 ('did you get as much help as you wanted?') is asked only when the family wanted extra help. A program drops children with K5Q22 skipped. What happens?",
    options: [
      { t: "Only families who wanted extra help remain, so effective navigation collapses in both groups and the gap changes, because the skip was information", correct: true, fb: "Yes, Trap 1 in a new file: n falls from {{exB.oaxaca.n:0}} to {{exB.falsification.skip_trap.n:0}}, navigation falls to {{exB.falsification.skip_trap.navigated_english}}% (English) and {{exB.falsification.skip_trap.navigated_other}}% (other-language), and the gap becomes {{ci:exB.falsification.skip_trap.gap}} pp. A skip because no help was needed is information." },
      { t: "Nothing, because skipped answers are missing at random and dropping them is harmless", fb: "The skip is caused by the answer to K5Q21; it is the opposite of random." },
      { t: "Only the standard errors change", fb: "The point estimates change too, because the analysed population changes." },
      { t: "It removes children without special health care needs, so the population becomes cleaner", fb: "Those were never in the population; the skip removes families who did not want extra help." } ] },
  "seminar-3": { q: "Seminar question 3: 'Your linear model predicts probabilities outside 0–1 for some children. Doesn't that invalidate it?'",
    options: [
      { t: "It is a known limitation of the LPM: we use it for exact additivity, disclose how many predictions fall outside 0–1, and show a Fairlie comparison", correct: true, fb: "Yes. The decomposition concerns group MEANS, which the LPM fits exactly; individual predictions outside [0,1] are not small here ({{primary.outside01_share_english:pct}}% of English-group and {{primary.outside01_share_other:pct}}% of other-language fitted values), so they are disclosed, and the logit comparison (Interaction 3) shows what is lost and gained." },
      { t: "No, because no linear model can predict outside 0–1 when the outcome is binary", fb: "The LPM can and does: in implicate 1, {{primary.outside01_english.0:0}} English-group and {{primary.outside01_other.0:0}} other-language fitted values fall outside [0, 1] (the core program prints all six implicates). Disclosing that is better than hiding it." },
      { t: "We should drop those children so that every prediction is a valid probability", fb: "That would select the sample on predicted values, a much worse problem." } ] }
};

/* Checklists for the writing tasks (self-explanation). One shared list of
   causal and over-claiming phrases, matched as whole words; any sentence that
   uses one is quoted back for the learner to review (see checklist() in app.js). */
var CAUSAL = ["cause", "causes", "caused", "causing", "due to", "because of", "effect of", "effects of",
  "drive", "drives", "drove", "driven by", "driving", "lead to", "leads to", "led to", "leading to",
  "result in", "results in", "resulted in", "responsible for", "prove", "proves", "proved", "proven", "proof", "would close", "would eliminate"];
window.WRITING = {
  exa: { minWords: 60, items: [
    { label: "Reports the preventive-visit gap", any: ["13.2", "13.22"], miss: "Give the gap: {{ci:exA.specs.PREVENTIVE_W2|A_all_blocks.lpm.gap}} pp." },
    { label: "Reports both methods", any: ["fairlie"], miss: "Report the Fairlie result next to the LPM one." },
    { label: "Addresses circularity", any: ["circular", "usual source", "without", "removed", "excluding"], miss: "Say what happens without the other access outcome (specification B)." },
    { label: "Mentions ordering dependence or another limitation", any: ["order", "limitation", "sequence", "reference"], miss: "Name one limitation, e.g. Fairlie's ordering dependence." },
    { label: "Avoids causal verbs", none: CAUSAL, badmsg: "Remove \"%s\": a decomposition is accounting." } ] },
  exb: { minWords: 60, items: [
    { label: "Reports the gap with its interval", any: [" ci ", " ci:", "(ci", "95%", "interval", "confidence"], miss: "Give the gap with its 95% CI: {{ci:exB.oaxaca.terms.gap}} pp." },
    { label: "Says the result is compatible with no gap, or imprecise", any: ["includes zero", "include zero", "includes 0", "compatible with", "imprecise", "uncertain", "cannot exclude", "cannot rule out", "could not exclude", "could not rule out", "not statistically significant", "not significant"], miss: "Say plainly that the interval includes zero, and what that does and does not mean." },
    { label: "Reports a robustness check", any: ["dfl", "reweight", "leave-one-year", "leave one year", "leaving out", "left out", "one year at a time", "period split", "2016-2021", "2016–2021", "2022-2025", "2022–2025", "original weights", "pre-revision", "weight revision", "revised weights", "skip"], miss: "Report one check: DFL, leave-one-year-out, the period split or the weight revision." },
    { label: "Avoids causal and over-claiming verbs", none: CAUSAL.concat(["no disparity", "no difference exists"]), badmsg: "Remove \"%s\": an interval that includes zero is not proof of no gap, and a decomposition is accounting." } ] },
  counterfactual: { minWords: 15, items: [
    { label: "States a counterfactual ('if ... had ...')", any: ["if ", "had the same", "were the same", "same distribution", "same mix", "same characteristics", "same levels"], miss: "Phrase it as: how much smaller would the gap be IF the other-language group had the English group's distribution of the measured characteristics?" },
    { label: "Names the measured characteristics / composition", any: ["characteristic", "covariate", "composition", "distribution", "symptom", "attention", "demograph", "access"], miss: "Say WHAT is being equalised: the distribution of measured covariates." },
    { label: "Keeps the outcome as REPORTED diagnosis", any: ["diagnos", "report", "told"], miss: "The outcome is caregiver-reported diagnosis, not ADHD itself." },
    { label: "Avoids causal language", none: CAUSAL, badmsg: "You used \"%s\". A decomposition is accounting; replace causal verbs with 'is associated with' or 'accounts for'." } ] },
  results: { minWords: 60, items: [
    { label: "Reports the sample size", any: ["12,977", "12977", " n=", " n = ", "children"], miss: "Give n ({{primary.n:0}})." },
    { label: "Reports the gap with its CI", any: ["9.77", "9.8"], miss: "Give the gap: {{ci:primary.terms.gap}} pp." },
    { label: "Reports the explained part with its CI", any: ["8.19", "8.2"], miss: "Give the explained part: {{ci:primary.terms.explained}} pp." },
    { label: "Reports the unexplained part and its uncertainty", any: ["1.58", "1.6", "unexplained"], miss: "Give the unexplained part and its CI: {{ci:primary.terms.unexplained}} pp." },
    { label: "Uses percentage points", any: ["percentage point", " pp", "points"], miss: "Differences of percentages are percentage points." },
    { label: "Says 'explained' is compositional / not causal", any: ["not causal", "compositional", "composition", "descriptive", "does not imply caus", "cannot establish"], miss: "Add one sentence: explained denotes measured covariate composition, not causes." },
    { label: "Avoids causal and over-claiming verbs", none: CAUSAL.concat(["no under-diagnosis", "no underdiagnosis", "rules out", "rule out"]), badmsg: "Remove \"%s\": the design cannot support it." },
    { label: "Names a sensitivity analysis", any: ["sensitivity", "same-case", "same sample", "same children", "without the preventive", "removing the preventive", "preventive visit removed", "total score", "reference"], miss: "Mention one sensitivity result, e.g. same-case without the preventive visit: explained {{sens.no_preventive_samecase.explained.est}} pp." } ] }
};
