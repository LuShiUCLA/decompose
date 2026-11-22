/* Decomposition Learning Lab - shared runtime.
 * No network calls. Learner progress is stored only in this browser's
 * localStorage (wrapped in try/catch; the lab works without it).
 * Every number shown comes from window.LAB (lab-data.js, generated from
 * program output by programs/build_lab_data.py).
 */
(function () {
  "use strict";
  var LAB = window.LAB || {};
  var KEY = "decomp-lab-progress-v1";

  // ---------- storage (per-viewer convenience only) ----------
  function loadProgress() {
    try { return JSON.parse(localStorage.getItem(KEY)) || { quiz: {}, done: {}, notes: {} }; }
    catch (e) { return { quiz: {}, done: {}, notes: {} }; }
  }
  function saveProgress(p) { try { localStorage.setItem(KEY, JSON.stringify(p)); } catch (e) { /* ignore */ } }
  var P = loadProgress();
  P.quiz = P.quiz || {}; P.done = P.done || {}; P.notes = P.notes || {};

  // ---------- numbers ----------
  function get(path) {
    var o = LAB;
    var parts = path.split(".");
    for (var i = 0; i < parts.length; i++) {
      if (o == null) return undefined;
      o = o[parts[i]];
    }
    return o;
  }
  function fmt(v, dp) {
    if (typeof v === "string") return v;
    if (typeof v !== "number" || !isFinite(v)) return "n/a";
    dp = dp == null ? 2 : dp;
    var s = Math.abs(v).toLocaleString("en-US", { minimumFractionDigits: dp, maximumFractionDigits: dp });
    return (v < 0 && Number(s.replace(/,/g, "")) !== 0 ? "−" : "") + s;
  }
  function num(path, dp) {
    var v = get(path);
    if (v === undefined) { console.error("Missing LAB value: " + path); return "[missing: " + path + "]"; }
    return fmt(v, dp);
  }
  function ci(path, dp) {
    return num(path + ".est", dp) + " (" + num(path + ".lo", dp) + ", " + num(path + ".hi", dp) + ")";
  }
  // template: {{path}} or {{path:dp}} or {{ci:path:dp}}
  function T(s) {
    // {{path:pct}} shows a stored proportion as a whole-number percentage
    s = String(s).replace(/\{\{([\w.|=\- ]+?):pct\}\}/g, function (_, path) {
      var v = get(path); return typeof v === "number" ? (100 * v).toFixed(0) : "[" + path + "]";
    });
    return String(s).replace(/\{\{(ci:)?([\w.|:=\- ]+?)(?::(\d))?\}\}/g, function (_, isci, path, dp) {
      dp = dp == null ? undefined : Number(dp);
      return isci ? ci(path, dp) : num(path, dp);
    });
  }
  function fillNumbers(root) {
    (root || document).querySelectorAll("[data-num]").forEach(function (el) {
      var dp = el.getAttribute("data-dp");
      el.textContent = num(el.getAttribute("data-num"), dp == null ? 2 : Number(dp));
    });
    (root || document).querySelectorAll("[data-ci]").forEach(function (el) {
      var dp = el.getAttribute("data-dp");
      el.textContent = ci(el.getAttribute("data-ci"), dp == null ? 2 : Number(dp));
    });
    (root || document).querySelectorAll("[data-t]").forEach(function (el) { el.innerHTML = T(el.innerHTML); el.removeAttribute("data-t"); });
  }

  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }

  // ---------- feedback helper ----------
  function feedback(el, ok, html) {
    el.className = "feedback " + (ok ? "good" : "bad");
    el.innerHTML = '<span class="tag">' + (ok ? "Correct. " : "Not yet. ") + "</span>" + html;
    el.classList.remove("hidden");
  }

  // ---------- retrieval-practice quiz engine ----------
  // QUIZ items live in quizzes.js. Each option carries its own diagnosis, so
  // a wrong answer is explained (what it implies, which trap it matches,
  // the next step), never just marked wrong.
  function renderQuiz(el) {
    var id = el.getAttribute("data-quiz");
    var q = (window.QUIZ || {})[id];
    if (!q) { el.textContent = "[quiz " + id + " missing]"; console.error("quiz missing " + id); return; }
    var name = "q-" + id;
    var html = '<fieldset><legend>' + (q.recall ? "Recall check (from " + esc(q.recall) + "): " : "Check: ") + T(q.q) + "</legend>";
    // Option order is shuffled once per item (seeded by its id, so it is the
    // same on every visit): the correct answer's position carries no cue.
    var order = q.options.map(function (_, i) { return i; });
    var h = 2166136261;
    for (var c = 0; c < id.length; c++) { h ^= id.charCodeAt(c); h = Math.imul(h, 16777619) >>> 0; }
    var slot = h % order.length;             // where the correct option goes
    for (var j = order.length - 1; j > 0; j--) {
      h = (Math.imul(h, 1664525) + 1013904223) >>> 0;
      var r = h % (j + 1), tmp = order[j]; order[j] = order[r]; order[r] = tmp;
    }
    var ci_ = q.options.findIndex(function (o) { return o.correct; });
    if (ci_ >= 0) { order.splice(order.indexOf(ci_), 1); order.splice(slot, 0, ci_); }
    order.forEach(function (i) {
      var o = q.options[i];
      html += '<label class="opt"><input type="radio" name="' + name + '" value="' + i + '"><span>' + T(o.t) + "</span></label>";
    });
    html += '</fieldset><div class="row"><button type="button" class="check">Check my answer</button></div>' +
      '<div class="feedback hidden" role="status" aria-live="polite"></div>';
    el.innerHTML = html;
    var fb = el.querySelector(".feedback");
    el.querySelector(".check").addEventListener("click", function () {
      var pick = el.querySelector("input:checked");
      if (!pick) { feedback(fb, false, "Pick one option first. Committing to an answer before seeing feedback is what makes retrieval practice work."); return; }
      var o = q.options[Number(pick.value)];
      feedback(fb, !!o.correct, T(o.fb));
      if (P.quiz[id] == null) { P.quiz[id] = !!o.correct; saveProgress(P); updateProgress(); }
    });
  }

  // ---------- free-text checklists (self-explanation tasks) ----------
  // Transparent keyword heuristics: the lab says what it looked for, and the
  // learner compares with the model answer. It is a checklist, not a grader.
  function checklist(text, rules) {
    var t = " " + text.toLowerCase() + " ";
    return rules.map(function (r) {
      var hit = r.any ? r.any.some(function (k) { return t.indexOf(k) >= 0; }) : true;
      // Causal wording cannot be judged reliably by keywords: "does not show
      // that X causes" is a correct disclaimer, "it is not surprising that X
      // causes" is a causal claim. So the checklist does not pass or fail it:
      // it quotes every sentence that uses a flagged word and asks the learner
      // to confirm the sentence negates it or reports someone else's claim.
      var sents = text.split(/(?<=[.!?;])\s+/);
      var hits = r.none ? sents.filter(function (sn) {
        var u = " " + sn.toLowerCase() + " ";
        return r.none.some(function (k) {
          var e = k.trim().replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
          return new RegExp("(^|[^a-z])" + e + "($|[^a-z])").test(u);
        });
      }) : [];
      if (r.none) return { ok: hits.length === 0, review: hits.length > 0, label: r.label,
        why: hits.length ? "Check each sentence below. If it asserts that something causes or proves the gap, rewrite it as accounting ('is associated with', 'accounts for'); if it is a disclaimer, it is fine.<br>" +
          hits.map(function (h) { return "&ldquo;" + esc(h.trim()) + "&rdquo;"; }).join("<br>") : (r.good || "") };
      return { ok: hit, label: r.label, why: hit ? (r.good || "") : r.miss };
    });
  }
  function wireWriting(el) {
    var rules = window.WRITING && window.WRITING[el.getAttribute("data-writing")];
    if (!rules) return;
    var id = el.getAttribute("data-writing");
    var ta = el.querySelector("textarea"), btn = el.querySelector("button.check"), out = el.querySelector(".feedback"), model = el.querySelector(".model");
    if (P.notes[id]) ta.value = P.notes[id];
    ta.addEventListener("input", function () { P.notes[id] = ta.value; saveProgress(P); });
    btn.addEventListener("click", function () {
      if (ta.value.trim().split(/\s+/).length < (rules.minWords || 10)) {
        feedback(out, false, "Write at least " + (rules.minWords || 10) + " words in your own words first; explaining it to yourself is the exercise.");
        return;
      }
      var res = checklist(ta.value, rules.items);
      // a sentence quoted for review is not a failure: colour by the other items
      var allok = res.every(function (r) { return r.ok || r.review; });
      out.className = "feedback " + (allok ? "good" : "bad");
      out.innerHTML = "<p><b>Checklist</b> (keyword-based, so read each line critically):</p><ul>" +
        res.map(function (r) { return "<li>" + (r.ok ? "✔ " : r.review ? "? " : "✖ ") + "<b>" + esc(r.label) + "</b>" + (r.why ? " — " + (r.review ? r.why : T(r.why)) : "") + "</li>"; }).join("") + "</ul>";
      out.classList.remove("hidden");
      if (model) model.classList.remove("hidden");
      P.done["writing-" + id] = true; saveProgress(P); updateProgress();
    });
  }

  // ---------- progress against the bar ----------
  function updateProgress() {
    var all = Object.keys(window.QUIZ || {});
    var answered = all.filter(function (k) { return P.quiz[k] != null; }).length;
    var correct = all.filter(function (k) { return P.quiz[k] === true; }).length;
    document.querySelectorAll("[data-progress]").forEach(function (el) {
      var bar = el.querySelector(".progress > div");
      if (bar) bar.style.width = (all.length ? 100 * answered / all.length : 0) + "%";
      var txt = el.querySelector(".ptext");
      if (txt) txt.textContent = answered + " of " + all.length + " checks attempted, " + correct + " right on first try" +
        (P.done.reproduced ? "; headline reproduced within ±0.1 pp ✔" : "; headline not yet reproduced");
    });
  }

  // ---------- reproduce-the-headline checker (the bar) ----------
  function wireReproduce(el) {
    var btn = el.querySelector("button"), out = el.querySelector(".feedback");
    btn.addEventListener("click", function () {
      var fields = [["gap", "primary.terms.gap.est"], ["explained", "primary.terms.explained.est"], ["unexplained", "primary.terms.unexplained.est"]];
      var msgs = [], ok = true;
      fields.forEach(function (f) {
        var v = parseFloat(el.querySelector("[name=" + f[0] + "]").value);
        var ref = get(f[1]);
        if (!isFinite(v)) { ok = false; msgs.push(f[0] + ": enter a number in percentage points (e.g. 9.77, not 0.0977)."); return; }
        var d = v - ref;
        if (Math.abs(d) <= 0.1) msgs.push(f[0] + ": " + fmt(v) + " ✔ within ±0.1 pp.");
        else {
          ok = false;
          var diag = Math.abs(v * 100 - ref) <= 0.1 ? " You entered a proportion; multiply by 100." :
            (f[0] === "explained" && Math.abs(v - get("fals.decomp_dropped_skips.explained")) < 0.1) ? " This matches the analysis with K4Q20R skips DROPPED (Trap 1). Recode S4Q01 = 2 as zero preventive visits." :
            (f[0] === "gap" && Math.abs(v - get("fals.decomp_dropped_skips.gap")) < 0.1) ? " This is the gap on the dropped-skip sample (n = " + num("fals.decomp_dropped_skips.n", 0) + "). Trap 1: recode S4Q01 = 2 as zero." :
            (Math.abs(v - get("variants.other_reference." + f[0])) < 0.1) ? " This matches the OTHER-language coefficient reference. The study uses English coefficients." :
            (Math.abs(v - get("variants.pooled_reference." + f[0])) < 0.1) ? " This matches the POOLED reference. The study uses English coefficients." :
            (Math.abs(v - get("sens.brief_method." + f[0] + ".est")) < 0.01) ? " This matches the design brief's figures: the earlier caregiver mental-health rule plus income averaged over the six imputations (Module 5, 'Three choices'). The study uses the reviewed rule and Rubin's rules." :
            (Math.abs(v - get("sens.earlier_caregiver_mh_rule." + f[0] + ".est")) < 0.1) ? " This matches the EARLIER caregiver mental-health rule (n = " + num("sens.earlier_caregiver_mh_rule.n", 0) + "), which codes caregiver mental health as 'not poor' when a present second caregiver did not answer. The study requires every present caregiver to have answered (Module 5)." :
            " Check your sample first (n should be " + num("primary.n", 0) + "), then the caregiver mental-health rule, then that you averaged over all six FPL implicates.";
          msgs.push(f[0] + ": " + fmt(v) + " is " + Math.abs(d).toFixed(3) + " pp away (the bar is ±0.1 pp)." + diag);
        }
      });
      out.className = "feedback " + (ok ? "good" : "bad");
      out.innerHTML = msgs.map(esc).join("<br>") + (ok ? "<br><b>You have reproduced the headline decomposition from the raw file.</b>" : "");
      out.classList.remove("hidden");
      if (ok) { P.done.reproduced = true; saveProgress(P); updateProgress(); }
    });
  }

  // ---------- page-level boot ----------
  function boot() {
    fillNumbers(document);
    document.querySelectorAll("[data-quiz]").forEach(renderQuiz);
    document.querySelectorAll("[data-writing]").forEach(wireWriting);
    document.querySelectorAll("[data-reproduce]").forEach(wireReproduce);
    var here = document.body.getAttribute("data-page");
    document.querySelectorAll("nav.mods a").forEach(function (a) { if (a.getAttribute("data-page") === here) a.setAttribute("aria-current", "page"); });
    if (here) { P.done["visited-" + here] = true; saveProgress(P); }
    var reset = document.getElementById("reset-progress");
    if (reset) reset.addEventListener("click", function () { P = { quiz: {}, done: {}, notes: {} }; saveProgress(P); updateProgress(); reset.textContent = "Progress cleared"; });
    updateProgress();
    if (window.PAGE_INIT) window.PAGE_INIT.forEach(function (f) { try { f(); } catch (e) { console.error(e); } });
  }
  window.LABRT = { get: get, fmt: fmt, num: num, ci: ci, T: T, esc: esc, feedback: feedback, fill: fillNumbers, progress: function () { return P; }, save: function () { saveProgress(P); updateProgress(); } };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot); else boot();
})();
