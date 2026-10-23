// Layout on every device: no sideways scrolling, large enough touch targets, no iOS zoom on inputs,
// and the answer keypad fits on the screen.
const { test, expect, TASK, open, press, isTouch, fillIntro, waitEnabled, advanceUntil } = require("./helpers");

const noSideScroll = async (page, where) => {
  const [sw, w] = await page.evaluate(() => [document.documentElement.scrollWidth, window.innerWidth]);
  expect(sw, `page wider than the screen on the ${where} page`).toBeLessThanOrEqual(w);
};
const minSize = async (locator, px, what) => {
  for (const el of await locator.all()) {
    const b = await el.boundingBox();
    expect(Math.min(b.width, b.height), `${what} at least ${px}px`).toBeGreaterThanOrEqual(px);
  }
};

test("every page fits the screen; touch targets and inputs are comfortable", async ({ page }, testInfo) => {
  test.setTimeout(120_000);
  const touch = isTouch(testInfo);
  await open(page, TASK);
  await fillIntro(page);
  await noSideScroll(page, "intro");
  const fontSizes = await page.locator("input[type=text], input[type=number], select").evaluateAll(els => els.map(e => parseFloat(getComputedStyle(e).fontSize)));
  for (const fs of fontSizes) expect(fs, "input text >= 16px (no zoom on iPhone)").toBeGreaterThanOrEqual(16);
  if (touch) await minSize(page.locator(".seg span"), 44, "Yes/No buttons");

  await press(page, page.locator("#start"), touch);
  await expect(page.getByRole("heading", { name: "Choose a theme" })).toBeVisible();
  await noSideScroll(page, "theme");
  if (touch) await minSize(page.locator(".opt-card"), 44, "theme options");
  await press(page, page.locator("#go"), touch);
  await waitEnabled(page, page.locator("#ok"));
  await noSideScroll(page, "volume");
  await press(page, page.locator("#ok"), touch);
  await noSideScroll(page, "practice instructions");
  await press(page, page.locator("#go"), touch);

  await advanceUntil(page, page.locator("#app .big"), { step: 250 });
  await noSideScroll(page, "digit");
  await advanceUntil(page, page.locator("#slots"), { step: 2000 });
  await noSideScroll(page, "answer");
  const done = await page.locator('#pad [data-k="done"]').boundingBox();
  const vh = await page.evaluate(() => window.innerHeight);
  expect(done.y + done.height, "Done key visible without scrolling").toBeLessThanOrEqual(vh);
  if (touch) await minSize(page.locator("#pad button"), 44, "keypad keys");
});
