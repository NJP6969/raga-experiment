// Quick checks (npm run test:smoke). With BASE_URL set they run against any copy of the site, e.g. the live one.
// They never upload anything: ?nosave=1, and the data server is blocked.
const { test, expect, fillIntro, press, isTouch } = require("./helpers");

test("@smoke task page loads with its theme files", async ({ page }) => {
  await page.goto("index.html?nosave=1&row=1");
  await expect(page.getByRole("heading", { name: "Welcome", exact: true })).toBeVisible();
  await expect(page.locator(".step-count")).toHaveText("Step 1 of 6");
  expect(await page.evaluate(() => typeof Theme === "object" && getComputedStyle(document.documentElement).getPropertyValue("--bg").trim() !== "")).toBe(true);
  await expect(page.locator("#infoNext")).toBeEnabled();
  await expect(page.locator("#progress")).toBeVisible();
});

test("@smoke intro leads to the theme page", async ({ page }, testInfo) => {
  await page.goto("index.html?nosave=1&row=1");
  await fillIntro(page);
  await press(page, page.locator("#start"), isTouch(testInfo));
  await expect(page.getByRole("heading", { name: "Choose a theme" })).toBeVisible();
  page.on("dialog", d => d.accept());
});

test("@smoke template page loads with the design files", async ({ page, request }) => {
  await page.goto("template.html");
  await expect(page.getByRole("heading", { name: "Page template" })).toBeVisible();
  expect(await page.evaluate(() => getComputedStyle(document.documentElement).getPropertyValue("--heading").trim())).not.toBe("");
  expect((await request.get("assets/tokens.json")).status(), "tokens.json").toBe(200);
});

test("@smoke stimulus check page and all four music files are served", async ({ page, request }) => {
  await page.goto("test.html");
  await expect(page.getByRole("heading", { name: "Stimulus check" })).toBeVisible();
  for (const f of ["A_raga_slow", "B_raga_fast", "C_western_slow", "D_western_fast"]) {
    const res = await request.head(`stimuli/${f}.mp3`);
    expect(res.status(), f).toBe(200);
    expect(res.headers()["content-type"], f).toMatch(/audio\/mpeg/);
  }
});
