// Shared fixtures and steps for the browser tests.
"use strict";
const fs = require("fs");
const { test: base, expect } = require("@playwright/test");

// Test mode: short lead-in and rest, no upload, fixed order (row 1 = ABECD).
const TASK = "index.html?fast=1&nosave=1&row=1";

// Every test: block the real data server (nothing may ever upload) and fail on any JavaScript error.
const test = base.extend({
  page: async ({ page }, use) => {
    const errors = [];
    page.on("pageerror", e => errors.push(e.message));
    await page.route(/pipe\.jspsych\.org/, r => r.abort());
    await use(page);
    expect(errors, "JavaScript errors on the page").toEqual([]);
  }
});

const isTouch = testInfo => !!testInfo.project.use.hasTouch;

async function open(page, url = TASK, { clock = true } = {}) {
  if (clock) await page.clock.install();       // lets the tests skip the 30 s lead-ins and digit timings
  await page.addInitScript(() => {             // record every digit the page shows, so answers can be checked
    window.__shown = [];
    let last = null;
    new MutationObserver(() => {
      const b = document.querySelector("#app .big");
      if (b && b !== last) { last = b; if (/^[1-9]$/.test(b.textContent.trim())) window.__shown.push(b.textContent.trim()); }
    }).observe(document, { childList: true, subtree: true });
  });
  await page.goto(url);
}

// Wait for a button that depends on audio loading: real time for the download, page time for its fallback timer.
async function waitEnabled(page, locator, maxMs = 60_000) {
  for (const t0 = Date.now(); Date.now() - t0 < maxMs;) {
    if (await locator.isEnabled()) return;
    await page.waitForTimeout(200);
    await page.clock.runFor(1000);
  }
  await expect(locator).toBeEnabled({ timeout: 1 });
}

// Fast-forward the page clock until the locator is visible.
async function advanceUntil(page, locator, { step = 500, max = 120_000 } = {}) {
  for (let t = 0; t <= max; t += step) {
    if (await locator.isVisible()) return;
    await page.clock.runFor(step);
  }
  await expect(locator).toBeVisible({ timeout: 1 });
}

async function press(page, locator, touch) { return touch ? locator.tap() : locator.click(); }

// First page: information and consent. Tick all three statements, then "I agree, continue".
async function acceptConsent(page) {
  for (const box of await page.locator("#consent input[type=checkbox]").all()) await box.check();
  await page.locator("#agree").click();
  await expect(page.getByRole("heading", { name: "About you" })).toBeVisible();
}

// Consent, then the "About you" page (everything except pressing Begin).
async function fillIntro(page, { course = "yes", name = "Test Student", roll = "2023102029", famC = "3", famH = "2", training = "0" } = {}) {
  if (await page.locator("#agree").isVisible()) await acceptConsent(page);
  await page.getByRole("radio", { name: course === "yes" ? "Yes" : "No", exact: true }).check();
  if (course === "yes") await page.fill("#pname", name);
  await page.fill("#pid", roll);
  await page.selectOption("#famC", famC);
  await page.selectOption("#famH", famH);
  await page.fill("#trn", training);
  await page.check("#hear");
}

// Type one recall answer: keypad taps on touch screens, keyboard otherwise.
async function enterDigits(page, digits, touch) {
  if (touch) {
    for (const d of digits) await page.locator(`#pad [data-k="${d}"]`).tap();
    await page.locator('#pad [data-k="done"]').tap();
  } else {
    await page.keyboard.type(digits);
    await page.keyboard.press("Enter");
  }
}

// Wait through one list's presentation, then answer with the digits that were shown (or `answer`).
async function doList(page, touch, { answer } = {}) {
  await advanceUntil(page, page.locator("#slots"), { step: 2000, max: 30_000 });
  const shown = (await page.evaluate(() => window.__shown.splice(0))).slice(-9).join("");
  const digits = answer ?? shown;
  await enterDigits(page, digits, touch);
  return { shown, typed: digits };
}

async function rate(page, value = 3, touch = false) {
  for (const sc of await page.locator(".scale").all()) await press(page, sc.locator(`button[data-v="${value}"]`), touch);
  await press(page, page.locator("#next"), touch);
}

function parseCSV(text) {
  const rows = []; let row = [], cell = "", q = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (q) { if (c === '"' && text[i + 1] === '"') { cell += '"'; i++; } else if (c === '"') q = false; else cell += c; }
    else if (c === '"') q = true;
    else if (c === ",") { row.push(cell); cell = ""; }
    else if (c === "\n") { row.push(cell); rows.push(row); row = []; cell = ""; }
    else cell += c;
  }
  if (cell || row.length) { row.push(cell); rows.push(row); }
  const [head, ...body] = rows;
  return body.map(r => Object.fromEntries(head.map((h, i) => [h, r[i]])));
}

async function downloadCSV(page, buttonSel) {
  const [dl] = await Promise.all([page.waitForEvent("download"), page.click(buttonSel)]);
  return parseCSV(fs.readFileSync(await dl.path(), "utf8"));
}

module.exports = { test, expect, TASK, isTouch, open, waitEnabled, advanceUntil, press, acceptConsent, fillIntro, enterDigits, doList, rate, parseCSV, downloadCSV };

// Intro page -> theme (setup) -> volume check, ending on the practice instructions page.
async function startSession(page, touch, intro = {}) {
  await fillIntro(page, intro);
  await press(page, page.locator("#start"), touch);
  await expect(page.getByRole("heading", { name: "Choose a theme" })).toBeVisible();
  await press(page, page.locator("#go"), touch);                       // keep the default (System)
  await waitEnabled(page, page.locator("#ok"));
  await press(page, page.locator("#ok"), touch);
  await expect(page.getByRole("heading", { name: "The task: number lists" })).toBeVisible();
}

// Practice instructions -> 2 practice lists -> baseline rating, ending on the "Ready" page.
async function doPractice(page, touch) {
  await press(page, page.locator("#go"), touch);
  for (let i = 0; i < 2; i++) await doList(page, touch);
  await advanceUntil(page, page.locator("#next"));
  await rate(page, 3, touch);
  await expect(page.getByRole("heading", { name: "Ready" })).toBeVisible();
}

// One block from its start page: lead-in, 8 lists, ratings, then the rest (skipped after the last block).
async function doBlock(page, touch, k) {
  await expect(page.getByRole("heading", { name: `Block ${k + 1} of 5` })).toBeVisible();
  await waitEnabled(page, page.locator("#go"));
  await press(page, page.locator("#go"), touch);
  for (let i = 0; i < 8; i++) await doList(page, touch);
  await advanceUntil(page, page.locator("#next"));
  await rate(page, 4, touch);
}

module.exports.startSession = startSession;
module.exports.doPractice = doPractice;
module.exports.doBlock = doBlock;
