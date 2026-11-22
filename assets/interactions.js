/* Interactions: calculator, reference switcher, logit vs LPM, falsification
 * sandbox, and the builder's three additions (prediction bars, seminar,
 * table export). Each initialiser runs only if its container exists. */
(function () {
  "use strict";
  window.PAGE_INIT = window.PAGE_INIT || [];
  var R = function () { return window.LABRT; };
  var BLOCKS = [
    ["demographics", "Demographics (age, sex, race, ethnicity, education, income, caregiver mental health)", "--b1"],
    ["concentration_fidget", "Concentration + fidgeting items (PSC-17)", "--b2"],
    ["other_attention", "Other attention items (PSC-17: motor, daydreams, distractible)", "--b3"],
    ["persistence_homework_calm", "Persistence, homework, calmness", "--b4"],
    ["access", "Access (insured, usual source, preventive visit)", "--b5"]
  ];
  function css(v) { return "var(" + v + ")"; }
  function el(id) { return document.getElementById(id); }

  // horizontal signed bars, scaled to a common max
  function hbars(container, rows, maxAbs) {
    var h = "";
    rows.forEach(function (r) {
      var pct = Math.min(100, 50 * Math.abs(r.v) / maxAbs);
      var left = r.v >= 0 ? 50 : 50 - pct;
      h += '<div class="hbar"><span class="lab">' + r.label + '</span><span class="track" aria-hidden="true">' +
        '<span class="zero" style="left:50%"></span><span class="fill" style="left:' + left + "%;width:" + pct + "%;background:" + r.color + '"></span></span>' +
        '<span class="n" style="text-align:right">' + R().fmt(r.v) + "</span></div>";
    });
    container.innerHTML = h;
  }
  // stacked bar of the gap: explained (+ blocks) and unexplained
  function stacked(container, parts, total) {
    var h = '<div class="bar" role="img" aria-label="' + parts.map(function (p) { return p.label + " " + R().fmt(p.v) + " pp"; }).join(", ") + '">';
    var scale = parts.reduce(function (s, p) { return s + Math.abs(p.v); }, 0) || 1;
    parts.forEach(function (p) {
      var w = 100 * Math.abs(p.v) / scale;
      h += '<span style="width:' + w + "%;background:" + p.color + (p.v < 0 ? ";background-image:repeating-linear-gradient(45deg,transparent 0 6px,rgba(255,255,255,.35) 6px 12px)" : "") + '" title="' + p.label + '">' + (w > 9 ? R().fmt(p.v) : "") + "</span>";
    });
    h += '</div><div class="legend">' + parts.map(function (p) { return '<span><i style="background:' + p.color + '"></i>' + p.label + ": " + R().fmt(p.v) + " pp" + (p.v < 0 ? " (negative, hatched)" : "") + "</span>"; }).join("") + "</div>";
    container.innerHTML = h;
  }

  // ======================= 1. LIVE DECOMPOSITION CALCULATOR ===================
  window.PAGE_INIT.push(function calculator() {
    var root = el("calculator"); if (!root) return;
    var L = window.LAB, gap = L.primary.terms.gap.est;
    var base = {}; BLOCKS.forEach(function (b) { base[b[0]] = L.primary.terms["block:" + b[0]].est; });
    var sel = root.querySelector("select"), rng = root.querySelector("input[type=range]"), out = root.querySelector(".calc-out"), lbl = root.querySelector(".scale-label");
    function draw() {
      var s = Number(rng.value) / 100, which = sel.value, vals = {}, ex = 0;
      BLOCKS.forEach(function (b) { vals[b[0]] = base[b[0]] * (b[0] === which ? s : 1); ex += vals[b[0]]; });
      lbl.textContent = (s * 100).toFixed(0) + "% of its observed covariate difference";
      var un = gap - ex;
      var parts = BLOCKS.map(function (b) { return { label: b[0].replace(/_/g, " "), v: vals[b[0]], color: css(b[2]) }; });
      parts.push({ label: "unexplained", v: un, color: css("--unexp") });
      stacked(out.querySelector(".stack"), parts, gap);
      out.querySelector(".nums").innerHTML = "Gap (observed, fixed): <b>" + R().fmt(gap) + " pp</b> &middot; Explained: <b>" + R().fmt(ex) +
        " pp</b> &middot; Unexplained: <b>" + R().fmt(un) + " pp</b> &middot; Explained share: <b>" + (100 * ex / gap).toFixed(1) + "%</b>";
    }
    sel.addEventListener("change", function () { rng.value = 100; draw(); });
    rng.addEventListener("input", draw);
    draw();
  });

  // worked-example fading (full -> partial -> blank) inside the calculator
  window.PAGE_INIT.push(function fading() {
    var root = el("fading"); if (!root) return;
    var C = window.LAB.primary.calculator;
    function row(block, col) {
      var b = C[block], i = b.columns.indexOf(col);
      return { me: b.mean_english[i], mo: b.mean_other[i], be: b.coef_english[i] };
    }
    var f = R().fmt;
    // step 1: full worked example
    var r1 = row("concentration_fidget", "PSCCONCENTRATE_W2_C");
    root.querySelector(".worked").innerHTML = "Trouble concentrating (0 = never, 1 = sometimes, 2 = often). English mean <b>" + f(r1.me, 4) +
      "</b>, other-language mean <b>" + f(r1.mo, 4) + "</b>, English coefficient <b>" + f(r1.be, 4) + "</b> (probability per step).<br>" +
      "Contribution = (" + f(r1.me, 4) + " − " + f(r1.mo, 4) + ") × " + f(r1.be, 4) + " = <b>" + f((r1.me - r1.mo) * r1.be, 5) +
      "</b> on the probability scale = <b>" + f(100 * (r1.me - r1.mo) * r1.be, 2) + " pp</b>.";
    // step 2: partial
    var r2 = row("concentration_fidget", "PSCFIDGET_W2_C");
    root.querySelector(".partial-given").innerHTML = "Fidgeting: English mean <b>" + f(r2.me, 4) + "</b>, other-language mean <b>" + f(r2.mo, 4) +
      "</b>, English coefficient <b>" + f(r2.be, 4) + "</b>. The difference in means is " + f(r2.me - r2.mo, 4) + ". Finish it: contribution in pp = ?";
    wireAnswer(root.querySelector(".partial"), 100 * (r2.me - r2.mo) * r2.be, 0.02, {
      prop: "You gave a proportion. Multiply by 100 to get percentage points.",
      other: "Use the ENGLISH coefficient (the study's reference). Multiply the difference in means (" + f(r2.me - r2.mo, 4) + ") by " + f(r2.be, 4) + ", then by 100.",
      sign: "Check the sign: English mean minus other-language mean."
    }, r2.bo);
    // step 3: blank - the whole access block
    var b = C.access, rows = "";
    b.columns.forEach(function (c, i) { rows += "<tr><td>" + c + '</td><td class="n">' + f(b.mean_english[i], 4) + '</td><td class="n">' + f(b.mean_other[i], 4) + '</td><td class="n">' + f(b.coef_english[i], 4) + "</td></tr>"; });
    root.querySelector(".blank-table").innerHTML = '<div class="tablewrap"><table><thead><tr><th>Variable</th><th class="n">English mean</th><th class="n">Other mean</th><th class="n">English coef.</th></tr></thead><tbody>' + rows + "</tbody></table></div>";
    var want = 0; b.columns.forEach(function (c, i) { want += 100 * (b.mean_english[i] - b.mean_other[i]) * b.coef_english[i]; });
    wireAnswer(root.querySelector(".blank"), want, 0.03, {
      prop: "You gave a proportion. Multiply by 100.",
      other: "Compute (English mean − other mean) × English coefficient for each of the three rows, add them, multiply by 100. The access block in the study is " + R().num("primary.terms.block:access.est") + " pp; small differences come from averaging over the six income implicates.",
      sign: "One sign is off: every term is English minus other-language."
    });
  });
  function wireAnswer(box, want, tol, diag) {
    var inp = box.querySelector("input"), btn = box.querySelector("button"), out = box.querySelector(".feedback");
    btn.addEventListener("click", function () {
      var v = parseFloat(inp.value);
      if (!isFinite(v)) { R().feedback(out, false, "Type a number, e.g. 1.23."); return; }
      if (Math.abs(v - want) <= tol) { R().feedback(out, true, "The answer is " + R().fmt(want, 2) + " pp. Every explained term is (difference in means) × (reference coefficient)."); return; }
      var msg = Math.abs(v * 100 - want) <= tol ? diag.prop : Math.abs(v + want) <= tol ? diag.sign : diag.other;
      R().feedback(out, false, msg);
    });
  }

  // reproduce-from-blocks + "what if access doubles" prediction
  window.PAGE_INIT.push(function rebuild() {
    var root = el("rebuild"); if (!root) return;
    var L = window.LAB.primary.terms, ex = L.explained.est, gap = L.gap.est, acc = L["block:access"].est;
    wireAnswer(root.querySelector(".q-ex"), ex, 0.011, { prop: "Multiply by 100.", sign: "Sum the five block values; signs as shown.", other: "Add the five block values in the table. Rounding each to 2 decimals can move the sum by up to 0.01." });
    wireAnswer(root.querySelector(".q-un"), gap - ex, 0.011, { prop: "Multiply by 100.", sign: "Unexplained = gap − explained.", other: "In a twofold decomposition the parts must add up: unexplained = gap − explained." });
    wireAnswer(root.querySelector(".q-double"), gap - ex - acc, 0.011, {
      prop: "Multiply by 100.",
      sign: "Doubling the access block ADDS one more access block to explained; the gap is fixed, so the unexplained part shrinks by the same amount.",
      other: "The observed gap does not change when you change an explanation of it. Explained rises by one access block (" + R().fmt(acc) + " pp), so unexplained falls from " + R().fmt(gap - ex) + " by the same amount. Try it with the slider below."
    });
  });

  // ======================= 2. REFERENCE-COEFFICIENT SWITCHER ===================
  window.PAGE_INIT.push(function switcher() {
    var root = el("switcher"); if (!root) return;
    var V = window.LAB.variants, out = root.querySelector(".sw-out"), txt = root.querySelector(".sw-text");
    var info = {
      english_reference: ["English coefficients (the study)", "Asks: if other-language children had the English group's covariate distribution, and the English group's covariate-diagnosis slopes applied, how much of the gap would close?"],
      other_reference: ["Other-language coefficients", "Uses the slopes estimated in the small other-language group (" + R().num("primary.n_other", 0) + " children, few diagnoses), so it is noisier, and weights the same covariate differences differently."],
      pooled_reference: ["Pooled coefficients (pooled model with a group indicator)", "A compromise slope from both groups; Jann (2008) describes this 'pooled' option, which includes a group indicator so the group difference is not absorbed into the slopes."],
      threefold: ["Threefold (endowments, coefficients, interaction)", "Separates a third piece, the interaction of differences in covariates and in slopes, instead of assigning it to one side."]
    };
    function show(k) {
      root.querySelectorAll("button[data-v]").forEach(function (b) { b.setAttribute("aria-pressed", b.getAttribute("data-v") === k ? "true" : "false"); });
      var v = V[k], parts;
      if (k === "threefold") parts = [{ label: "endowments", v: v.endowments, color: css("--exp") }, { label: "coefficients", v: v.coefficients, color: css("--unexp") }, { label: "interaction", v: v.interaction, color: css("--res") }];
      else parts = [{ label: "explained", v: v.explained, color: css("--exp") }, { label: "unexplained", v: v.unexplained, color: css("--unexp") }];
      stacked(out, parts, v.gap);
      txt.innerHTML = "<b>" + info[k][0] + ".</b> " + info[k][1] + " The gap is " + R().fmt(v.gap) + " pp in every version: only the split moves.";
    }
    root.querySelectorAll("button[data-v]").forEach(function (b) { b.addEventListener("click", function () { show(b.getAttribute("data-v")); }); });
    show("english_reference");
  });

  // ======================= 3. LOGIT VS LPM ===================================
  window.PAGE_INIT.push(function logit() {
    var root = el("logit"); if (!root) return;
    var btn = root.querySelector("button.reveal"), out = root.querySelector(".lg-out"), fb = root.querySelector(".feedback");
    btn.addEventListener("click", function () {
      var pick = root.querySelector("input[name=lgpred]:checked");
      if (!pick) { R().feedback(fb, false, "Make a prediction first. The point is to see whether your expectation matches the result."); return; }
      var G = window.LAB.logit, f = R().fmt;
      var rows = [["Linear probability model", G.lpm_explained, G.lpm_unexplained, G.lpm_residual],
        ["Logit, plugged in at the group means", G.naive_explained, G.naive_unexplained, G.naive_residual],
        ["Logit, Fairlie-style (average of predicted probabilities)", G.fairlie_explained, G.fairlie_unexplained, G.fairlie_residual]];
      out.innerHTML = '<div class="tablewrap"><table><thead><tr><th>Method (same ' + R().num("logit.n", 0) + ' children, same covariates)</th><th class="n">Explained</th><th class="n">Unexplained</th><th class="n">Gap − explained − unexplained</th></tr></thead><tbody>' +
        rows.map(function (r) { return "<tr><td>" + r[0] + '</td><td class="n">' + f(r[1]) + '</td><td class="n">' + f(r[2]) + '</td><td class="n"><b>' + f(r[3]) + "</b></td></tr>"; }).join("") +
        "</tbody></table></div><p>Observed gap on this sample: <b>" + f(G.gap) + " pp</b>.</p>";
      out.classList.remove("hidden");
      var said = pick.value;
      var good = said === "naive-no";
      R().feedback(fb, good, (good ? "" : "Look at the middle row. ") +
        "The naive logit parts leave " + f(G.naive_residual) + " pp unaccounted for: the logistic curve of the average covariate profile is not the average of the curves (Jensen's inequality). " +
        "The LPM residual is exactly 0 because a linear model with an intercept passes through the group means. Fairlie's approach restores the total by averaging predicted probabilities, but its detailed parts then depend on the order in which variables are switched (Exercise A).");
    });
  });

  // ======================= 4. FALSIFICATION SANDBOX ===========================
  var CASES = [
    { id: "skips", title: "Case A: a preventive-visit rate that looks too good",
      pred: "lower", hint: "Which children are missing from this output, and would they have had a preventive visit?",
      wrong: function (f, n) { return "Preventive visit in past year: English <b>" + n("fals.preventive_english.dropped_skips") + "%</b>, other-language <b>" + n("fals.preventive_other.dropped_skips") + "%</b> (" + n("fals.preventive_english.n_dropped", 0) + " and " + n("fals.preventive_other.n_dropped", 0) + " children). In the decomposition, n = " + n("fals.decomp_dropped_skips.n", 0) + ", gap " + n("fals.decomp_dropped_skips.gap") + " pp, explained " + n("fals.decomp_dropped_skips.explained") + " pp."; },
      right: function (f, n) { return "Correct coding: English <b>" + n("fals.preventive_english.correct") + "%</b>, other-language <b>" + n("fals.preventive_other.correct") + "%</b>. Decomposition n = " + n("primary.n", 0) + ", gap " + n("primary.terms.gap.est") + " pp, explained " + n("primary.terms.explained.est") + " pp."; },
      errors: [["skip", true, "Right. K4Q20R is skipped when S4Q01 = 2 (no medical visit at all). Treating the skip as missing deletes exactly the children with no care."],
               ["weights", false, "Weights would change the rate somewhat, but they cannot push both groups to ~98%. Look at who is missing: compare n with and without the skip."],
               ["subset", false, "Subsetting affects standard errors, not the point estimate of a rate. The point estimate itself is wrong here."],
               ["currcov", false, "That is Trap 2 (insurance). This output is about preventive visits; read the K4Q20R Universe column."]],
      bias: [["up", true, "Right. Dropping skips conditions on having had a visit, so the rate is pushed up, and more so for the other-language group (more no-visit children), which even reverses the sign of the language gap in preventive care."],
             ["down", false, "The children removed are those with NO visit, i.e. zeros. Removing zeros raises a rate."],
             ["none", false, "Compare the two outputs: the rates move by more than 10 pp."]] },
    { id: "currcov", title: "Case B: an insurance rate from the wrong variable",
      pred: "lower", hint: "Open the Variable List row for the insurance variable this output used and read its Description.",
      wrong: function (f, n) { return "Currently insured (using CURRCOV): English <b>" + n("fals.insured_english.currcov") + "%</b>, other-language <b>" + n("fals.insured_other.currcov") + "%</b>. Decomposition explained part " + n("fals.decomp_currcov.explained", 4) + " pp; access block " + n("fals.decomp_currcov.access", 4) + " pp."; },
      right: function (f, n) { return "Using CURRINS: English <b>" + n("fals.insured_english.currins") + "%</b>, other-language <b>" + n("fals.insured_other.currins") + "%</b>. Explained " + n("primary.terms.explained.est", 4) + " pp; access block " + n("primary.terms.block:access.est", 4) + " pp. The two variables disagree for " + n("fals.currins_currcov_disagree_primary", 0) + " children aged 6–17 (" + n("fals.currins_currcov_disagree_all", 0) + " in the whole cohort)."; },
      errors: [["currcov", true, "Right. CURRCOV is the raw question; the Variable List labels it '(Use CURRINS)'. CURRINS is the Census-edited indicator that does not count Indian Health Service-only or religious health-share-only coverage as insurance."],
               ["skip", false, "Insurance has no skip pattern here (Universe: All Children). Read the Description column of CURRCOV."],
               ["weights", false, "Same weights in both outputs; only the variable changed."],
               ["subset", false, "This is a variable-choice error, not a variance error."]],
      bias: [["up", true, "Right. CURRCOV counts some coverage that CURRINS excludes, so insured rates are slightly higher (here by " + "{{fals.insured_english.currcov}} vs {{fals.insured_english.currins}} in English households). Honest lesson: for the ADHD decomposition the effect is tiny. The point is that the error is invisible unless you check which variable you read."],
             ["down", false, "CURRINS excludes some coverage types; CURRCOV includes them, so CURRCOV is higher, not lower."],
             ["none", false, "Small, but not zero: compare the rates to two decimals, and count the disagreeing children."]] },
    { id: "subset", title: "Case C: a standard error from a pre-subset file",
      pred: "about the same", hint: "The rate is unchanged, so look at how the design was declared: which PSUs does the variance formula see?",
      predNote: function (p, n) {
        var w = n("fals.subset_vs_domain.remove.se", 3), r = n("fals.subset_vs_domain.domain.se", 3);
        if (p === "about the same") return "Your prediction (about the same) matched: the corrected SE is " + r + " pp against " + w + " pp in this output, a difference of well under 1%.";
        if (p === "higher") return "Strictly, you are right: the corrected SE (" + r + " pp) is a little higher than this output's (" + w + " pp). The difference is well under 1%, so in practice it is about the same. The damage is to the design, not to this one number.";
        return "The corrected SE (" + r + " pp) is not lower; it is a little higher than this output's (" + w + " pp), and the two are about the same.";
      },
      wrong: function (f, n) { return "Analyst kept only other-language children aged 6–17, then declared the survey design: ADHD rate " + n("fals.subset_vs_domain.remove.est") + "%, SE <b>" + n("fals.subset_vs_domain.remove.se", 3) + " pp</b>, design df " + n("fals.subset_vs_domain.remove.df", 0) + "; " + n("fals.subset_vs_domain.remove.singletons", 0) + " strata now have a single PSU (the software must drop or 'adjust' them; 'adjust' gives SE " + n("fals.subset_vs_domain.adjust.se", 3) + ")."; },
      right: function (f, n) { return "Domain estimation on the full design: same rate " + n("fals.subset_vs_domain.domain.est") + "%, SE <b>" + n("fals.subset_vs_domain.domain.se", 3) + " pp</b>, design df " + n("fals.subset_vs_domain.domain.df", 0) + ", no singleton strata."; },
      errors: [["subset", true, "Right. Subsetting before declaring the design throws away the PSUs with no domain members, creates singleton strata and changes the degrees of freedom."],
               ["skip", false, "No recode changed here; the point estimate is identical in both outputs."],
               ["currcov", false, "No variable changed; only the design declaration did."],
               ["weights", false, "The weights are identical; what changed is which PSUs the variance formula sees."]],
      bias: [["down", true, "Right in direction: here the pre-subset SE is slightly smaller. Honest lesson: in this file the difference is tiny (about 0.3%), but the singleton strata force an arbitrary choice and the df drops from 21,666 to 765. In other files, especially with few PSUs per stratum, it can be much larger. Use domain estimation (R: subset() of a full design; Stata: svy, subpop())."],
             ["up", false, "Compare the two SEs to three decimals."],
             ["none", true, "Also right on magnitude: the SE moves only in the third decimal (about 0.3%). The lesson is the design, not the size: singleton strata appear and the df falls from 21,666 to 765, and in files with few PSUs per stratum the difference can be much larger."]] },
    { id: "modeln", title: "Case D: a sample size that was 'corrected'",
      pred: "lower", hint: "Count the children with complete covariates but no ADHD answer.",
      wrong: function (f, n) { return "Methods text: 'The decomposition included <b>" + n("fals.model_n.design_matrix_n", 0) + "</b> children with complete covariates.'"; },
      right: function (f, n) { return "The models were fitted on <b>" + n("fals.model_n.model_n", 0) + "</b> children: " + n("fals.model_n.missing_outcome", 0) + " children had complete covariates but no ADHD answer, so they cannot enter a regression of that outcome."; },
      errors: [["modeln", true, "Right. Model n = rows with complete covariates AND an observed outcome. Reporting the design-matrix n describes a sample that was never analysed."],
               ["skip", false, "No recode is involved; it is a reporting error about who was analysed."],
               ["subset", false, "Not a variance issue: the estimates are the same, only the reported n is wrong."],
               ["currcov", false, "Not a variable choice; count rows with a missing outcome."]],
      bias: [["up", true, "Right: it overstates the analysed sample by " + "{{fals.model_n.missing_outcome:0}}" + " children; a reader cannot reproduce your n."],
             ["down", false, "The reported number is larger than the analysed number."],
             ["none", false, "It does not change the estimates, but it misreports the sample; reproducibility is part of correctness."]] }
  ];
  var ERRLAB = { skip: "Skip pattern treated as missing (K4Q20R / S4Q01)", currcov: "Wrong insurance variable (CURRCOV instead of CURRINS)",
    subset: "Pre-subsetting instead of domain estimation", weights: "Weights not applied", modeln: "Model n replaced by design-matrix n" };
  var BIASLAB = { up: "Overstates (estimate or n too high)", down: "Understates (estimate or SE too low)", none: "No meaningful effect (about the same)" };
  window.PAGE_INIT.push(function sandbox() {
    document.querySelectorAll("[data-cases]").forEach(sandboxIn);
  });
  function sandboxIn(root) {
    var n = function (p, dp) { return R().num(p, dp); };
    var want = (root.getAttribute("data-cases") || "skips,currcov,subset,modeln").split(",");
    root.innerHTML = CASES.map(function (c, ci) {
      if (want.indexOf(c.id) < 0) return "";
      return '<section class="screen" id="case-' + c.id + '"><h3>' + c.title + "</h3>" +
        '<fieldset><legend>Step 1. Before you look closely: what do you expect the correct value to be, relative to this output?</legend>' +
        ["higher", "lower", "about the same"].map(function (o) { return '<label class="opt"><input type="radio" name="pred-' + c.id + '" value="' + o + '"><span>' + o + "</span></label>"; }).join("") + "</fieldset>" +
        '<p class="wrong-out"><b>Output to audit:</b> ' + c.wrong(R().fmt, n) + "</p>" +
        '<fieldset><legend>Step 2. Name the error</legend>' + c.errors.map(function (e, i) { return '<label class="opt"><input type="radio" name="err-' + c.id + '" value="' + i + '"><span>' + ERRLAB[e[0]] + "</span></label>"; }).join("") + "</fieldset>" +
        '<fieldset><legend>Step 3. Direction of the bias</legend>' + c.bias.map(function (e, i) { return '<label class="opt"><input type="radio" name="bias-' + c.id + '" value="' + i + '"><span>' + BIASLAB[e[0]] + "</span></label>"; }).join("") + "</fieldset>" +
        '<div class="row"><button type="button" data-case="' + ci + '">Check my diagnosis</button></div><div class="feedback hidden" role="status" aria-live="polite"></div>' +
        '<p class="right-out hidden"><b>Corrected output, side by side:</b> ' + c.right(R().fmt, n) + "</p>" +
        '<p class="causal hidden"><strong>Reminder:</strong> fixing a coding error changes what the numbers describe; it never turns an explained share into a cause.</p></section>';
    }).join("");
    root.querySelectorAll("button[data-case]").forEach(function (b) {
      b.addEventListener("click", function () {
        var c = CASES[Number(b.getAttribute("data-case"))], sec = el("case-" + c.id), fb = sec.querySelector(".feedback");
        var p = sec.querySelector("input[name=pred-" + c.id + "]:checked"), e = sec.querySelector("input[name=err-" + c.id + "]:checked"), d = sec.querySelector("input[name=bias-" + c.id + "]:checked");
        if (!p || !e || !d) { R().feedback(fb, false, "Answer all three steps first: prediction, error, direction. The lab only reveals the corrected output after you commit."); return; }
        var E = c.errors[Number(e.value)], B = c.bias[Number(d.value)];
        var ok = E[1] && B[1];
        var predMsg = c.predNote ? c.predNote(p.value, n) : p.value === c.pred ? "Your prediction (" + p.value + ") matched." :
          "You predicted " + p.value + "; the corrected value is " + (c.pred === "lower" ? "lower than" : "about the same as") + " this output. Ask what you were picturing when you predicted.";
        R().feedback(fb, ok, "<b>Your diagnosis</b> (error and direction) " + (ok ? "is right." : "needs another look.") + "<br><b>Error:</b> " + R().T(E[2]) + "<br><b>Direction:</b> " + R().T(B[2]) + "<br><b>Your prediction</b> (not graded): " + predMsg);
        if (E[1]) { sec.querySelector(".right-out").classList.remove("hidden"); sec.querySelector(".causal").classList.remove("hidden"); }
        else fb.innerHTML += "<br>Smallest next step: " + c.hint + " The corrected output appears once you name the error.";
        var P = R().progress(); if (P.done["sandbox-" + c.id] == null) { P.done["sandbox-" + c.id] = ok; R().save(); }
      });
    });
  }

  // ======================= ADDITION 1: predict the split =====================
  window.PAGE_INIT.push(function predictBars() {
    var root = el("predict-bars"); if (!root) return;
    var T = window.LAB.primary.terms, gap = T.gap.est;
    var items = BLOCKS.map(function (b) { return [b[0], b[1], b[2], T["block:" + b[0]].est]; }).concat([["unexplained", "Unexplained (what the covariates do not account for)", "--unexp", T.unexplained.est]]);
    var form = root.querySelector(".pb-form");
    form.innerHTML = items.map(function (it) {
      return '<div class="hbar"><label class="lab" for="pb-' + it[0] + '">' + it[1] + '</label><input id="pb-' + it[0] + '" type="range" min="-2" max="10" step="0.1" value="' + (gap / 6).toFixed(1) + '"><output for="pb-' + it[0] + '">' + (gap / 6).toFixed(1) + "</output></div>";
    }).join("");
    var sumEl = root.querySelector(".pb-sum");
    function sum() { var s = 0; items.forEach(function (it) { var i = el("pb-" + it[0]); i.nextElementSibling.textContent = Number(i.value).toFixed(1); s += Number(i.value); }); sumEl.textContent = "Your parts add to " + s.toFixed(1) + " pp; the gap is " + R().fmt(gap) + " pp."; return s; }
    form.addEventListener("input", sum); sum();
    root.querySelector("button").addEventListener("click", function () {
      var err = 0, rows = [];
      items.forEach(function (it) { var v = Number(el("pb-" + it[0]).value); err += Math.abs(v - it[3]); rows.push({ label: it[0].replace(/_/g, " ") + " (you " + v.toFixed(1) + ")", v: it[3], color: css(it[2]) }); });
      hbars(root.querySelector(".pb-out"), rows, Math.max.apply(null, items.map(function (i) { return Math.abs(i[3]); })) * 1.1);
      var s = sum(), fb = root.querySelector(".feedback");
      R().feedback(fb, err < 4, "Total absolute prediction error: <b>" + err.toFixed(1) + " pp</b>" + (Math.abs(s - gap) > 0.2 ? ". Your parts did not add to the gap: in a twofold LPM decomposition they must." : ".") +
        " The bars show the actual split. Compare them with your prediction: here most of the gap tracks caregiver-reported attention items and little tracks access. Modules 2 to 5 examine why, and what that does and does not mean.");
    });
  });

  // ======================= ADDITION 3: export a manuscript table =============
  window.PAGE_INIT.push(function exporter() {
    var root = el("exporter"); if (!root) return;
    var src = window.LAB.core, status = root.querySelector(".ex-status");
    function table(core) {
      var t = core.primary.terms, f = function (d) { return R().fmt(d.est) + " (" + R().fmt(d.lo) + ", " + R().fmt(d.hi) + ")"; };
      var lines = ["| Component | Percentage points (95% CI) |", "|---|---|"];
      [["Gap (English − other-language)", "gap"], ["Explained (compositional)", "explained"], ["  Demographics", "block:demographics"], ["  Concentration + fidgeting", "block:concentration_fidget"],
       ["  Other attention items", "block:other_attention"], ["  Persistence, homework, calmness", "block:persistence_homework_calm"], ["  Access", "block:access"], ["Unexplained", "unexplained"]]
        .forEach(function (r) { lines.push("| " + r[0] + " | " + f(t[r[1]]) + " |"); });
      lines.push("", "Twofold Oaxaca–Blinder decomposition on the linear probability model, English-household coefficients as reference; n = " + core.primary.n.toLocaleString("en-US") +
        " children aged 6–17 (NSCH-LC 2024). Survey-weighted (FWC), Taylor-linearised over strata and PSUs (households), Rubin-pooled over six income implicates. " +
        "'Explained' denotes differences in measured covariate composition and does not identify causes.");
      return lines.join("\n");
    }
    function show(core, label) { root.querySelector("pre").textContent = table(core); status.textContent = label; }
    show(src, "Showing the lab's reference run.");
    root.querySelector("input[type=file]").addEventListener("change", function (e) {
      var file = e.target.files[0]; if (!file) return;
      var rd = new FileReader();
      rd.onload = function () {
        try { var j = JSON.parse(rd.result); if (!j.primary || !j.primary.terms) throw new Error("not a core_results.json"); show(j, "Showing YOUR run (" + file.name + "), read locally; nothing was uploaded."); }
        catch (err) { status.textContent = "That file is not a core_results.json written by programs/core/decomposition_lab_core.py (" + err.message + ")."; }
      };
      rd.readAsText(file);
    });
    root.querySelector("button.dl").addEventListener("click", function () {
      var blob = new Blob([root.querySelector("pre").textContent], { type: "text/markdown" });
      var a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "decomposition_table.md"; document.body.appendChild(a); a.click(); a.remove();
    });
  });
})();
