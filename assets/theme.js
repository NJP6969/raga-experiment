/* Theme choice (system / light / dark), shared by every page.
   Load it in <head> after tokens.css and theme.css so the page never flashes the wrong colours.
   "system" (the default) follows the device setting, including changes while the page is open. */
(function () {
  "use strict";
  var KEY = "raga_theme", CHOICES = ["system", "light", "dark"], listeners = [];
  var mq = window.matchMedia ? window.matchMedia("(prefers-color-scheme: dark)") : null;
  var root = document.documentElement;

  function get() {
    try { var v = localStorage.getItem(KEY); return CHOICES.indexOf(v) >= 0 ? v : "system"; } catch (e) { return "system"; }
  }
  function resolved(choice) {
    choice = choice || get();
    return choice === "system" ? (mq && mq.matches ? "dark" : "light") : choice;
  }
  function apply(choice) {
    if (choice === "light" || choice === "dark") root.setAttribute("data-theme", choice);
    else root.removeAttribute("data-theme");
    root.setAttribute("data-theme-choice", choice);
    var meta = document.querySelector('meta[name="theme-color"]');      // phone browser bar matches the page
    if (meta) { var bg = getComputedStyle(root).getPropertyValue("--bg").trim(); if (bg) meta.setAttribute("content", bg); }
  }
  function notify() { var c = get(), r = resolved(c); listeners.forEach(function (fn) { try { fn(c, r); } catch (e) {} }); }
  function set(choice) {
    if (CHOICES.indexOf(choice) < 0) choice = "system";
    try { localStorage.setItem(KEY, choice); } catch (e) {}
    apply(choice); notify();
  }
  function onChange(fn) { listeners.push(fn); }
  if (mq) {
    var follow = function () { apply(get()); notify(); };
    if (mq.addEventListener) mq.addEventListener("change", follow); else if (mq.addListener) mq.addListener(follow);
  }
  apply(get());

  // Any theme switch on the page (see theme.css) works without page code:
  // <div class="theme-switch" role="group" aria-label="Theme"><button type="button" data-theme-choice="light">Light</button>…</div>
  function wireSwitches() {
    var btns = [].slice.call(document.querySelectorAll(".theme-switch [data-theme-choice]"));
    if (!btns.length) return;
    var mark = function () { var c = get(); btns.forEach(function (b) { b.setAttribute("aria-pressed", String(b.getAttribute("data-theme-choice") === c)); }); };
    btns.forEach(function (b) { b.addEventListener("click", function () { set(b.getAttribute("data-theme-choice")); }); });
    onChange(mark); mark();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", wireSwitches); else wireSwitches();

  window.Theme = { KEY: KEY, CHOICES: CHOICES, get: get, set: set, resolved: resolved, onChange: onChange };
})();
