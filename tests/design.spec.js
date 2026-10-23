// Design system: assets/tokens.json (the source) -> assets/tokens.css (generated) -> assets/theme.css (shared
// styles) -> every page. Checks the generated file is current, the pages use only the tokens, and the
// starter page (template.html) shows every component in both themes.
const fs = require("fs");
const path = require("path");
const { test, expect, TASK, fillIntro, press, isTouch } = require("./helpers");
const { build, SRC, OUT } = require("../tools/build-tokens");

const ROOT = path.join(__dirname, "..");
const json = JSON.parse(fs.readFileSync(SRC, "utf8"));
const colours = set => Object.fromEntries(Object.entries(json[set].color).filter(([k]) => !k.startsWith("$")).map(([k, v]) => [k, v.$value]));
const LIGHT = colours("light"), DARK = colours("dark");
const lf = s => s.replace(/\r\n/g, "\n");
const onlyOnce = testInfo => test.skip(testInfo.project.name !== "desktop", "file check: runs once, on the desktop project");

test.describe("design tokens", () => {
  test("tokens.css is up to date with tokens.json (run `npm run tokens` after editing it)", async ({}, testInfo) => {
    onlyOnce(testInfo);
    expect(lf(fs.readFileSync(OUT, "utf8"))).toBe(lf(build()));
  });

  test("light and dark name the same colours", async ({}, testInfo) => {
    onlyOnce(testInfo);
    expect(Object.keys(DARK)).toEqual(Object.keys(LIGHT));
    for (const v of [...Object.values(LIGHT), ...Object.values(DARK)]) expect(v).toMatch(/^#[0-9a-f]{6}$/i);
  });

  test("pages take every colour from the tokens", async ({}, testInfo) => {
    onlyOnce(testInfo);
    for (const page of ["index.html", "test.html", "template.html"]) {
      const html = fs.readFileSync(path.join(ROOT, page), "utf8");
      expect(html, `${page} loads tokens.css, then theme.css, then theme.js`).toMatch(
        /<link rel="stylesheet" href="assets\/tokens\.css">\s*<link rel="stylesheet" href="assets\/theme\.css">\s*<script src="assets\/theme\.js"><\/script>/);
      expect(html.match(/<meta name="theme-color" content="(#[0-9a-f]{6})">/i)[1], `${page} browser bar starts as the light page colour`).toBe(LIGHT.bg);
      const styles = [...html.matchAll(/<style>([\s\S]*?)<\/style>|style="([^"]*)"/g)].map(m => m[1] || m[2]).join("\n");
      expect(styles.match(/#[0-9a-f]{3,8}\b|rgba?\(|hsla?\(/gi), `${page} has a hard-coded colour; use a token`).toBeNull();
    }
  });
});

test.describe("template page", () => {
  test("shows headings, colours, buttons, fields, notices and tables", async ({ page }) => {
    await page.goto("template.html");
    for (const h of ["Page template", "Start a new page", "Headings and text", "Colours", "Page layout", "Buttons", "Form fields", "Notices, progress and tables"])
      await expect(page.getByRole("heading", { name: h, exact: true })).toBeVisible();
    for (const part of [".site-header .brand", ".page-head .lead", ".page-nav .back-link", ".step-count", ".steps", ".checklist", ".facts", ".checks .check", ".actions", ".site-footer"])
      await expect(page.locator(part).first(), part).toBeVisible();
    await expect(page.getByRole("button", { name: "Continue", exact: true })).toBeEnabled();
    await expect(page.getByRole("button", { name: "Not yet" })).toBeDisabled();
    await expect(page.getByRole("radio", { name: "Yes" })).toBeChecked();
    await expect(page.getByRole("progressbar")).toBeVisible();
  });

  test("colour table lists every token with its light and dark value, whatever the page shows", async ({ page }) => {
    await page.emulateMedia({ colorScheme: "dark" });
    await page.goto("template.html");
    const rows = await page.locator("#colourRows tr").evaluateAll(trs => trs.map(tr => [tr.dataset.token, ...[...tr.querySelectorAll("td code")].slice(1).map(c => c.textContent)]));
    expect(rows).toEqual(Object.keys(LIGHT).map(k => [k, LIGHT[k], DARK[k]]));
  });

  test("headings use the heading font and colour", async ({ page }) => {
    await page.goto("template.html");
    const [got, want] = await page.locator("h1").first().evaluate(h => {
      const probe = document.createElement("span");
      probe.style.cssText = "color:var(--heading); font-family:var(--font-heading)";
      document.body.append(probe);
      const pick = el => { const cs = getComputedStyle(el); return [cs.fontFamily, cs.color]; };
      const r = [pick(h), pick(probe)]; probe.remove(); return r;
    });
    expect(got).toEqual(want);
  });

  test("theme switch sets the theme for every page", async ({ page }) => {
    await page.emulateMedia({ colorScheme: "light" });
    await page.goto("template.html");
    const group = page.getByRole("group", { name: "Theme" });
    await expect(group.getByRole("button", { name: "System" })).toHaveAttribute("aria-pressed", "true");
    await group.getByRole("button", { name: "Dark" }).click();
    await expect(group.getByRole("button", { name: "Dark" })).toHaveAttribute("aria-pressed", "true");
    expect(await page.evaluate(() => getComputedStyle(document.documentElement).getPropertyValue("--bg").trim())).toBe(DARK.bg);
    await page.goto(TASK);
    expect(await page.evaluate(() => Theme.get())).toBe("dark");
  });

  test("fits the screen (no sideways scrolling)", async ({ page }) => {
    for (const url of ["template.html", "test.html"]) {
      await page.goto(url);
      const [sw, w] = await page.evaluate(() => [document.documentElement.scrollWidth, window.innerWidth]);
      expect(sw, `${url} wider than the screen`).toBeLessThanOrEqual(w);
    }
  });
});

test("theme page swatches show their own palette, whatever the page shows", async ({ page }, testInfo) => {
  await page.emulateMedia({ colorScheme: "dark" });
  await page.goto(TASK);
  await fillIntro(page);
  await press(page, page.locator("#start"), isTouch(testInfo));
  await expect(page.getByRole("heading", { name: "Choose a theme" })).toBeVisible();
  const bg = sel => page.locator(sel).evaluate(el => getComputedStyle(el).getPropertyValue("--bg").trim());
  expect(await bg(".sw-light")).toBe(LIGHT.bg);
  expect(await bg(".sw-dark")).toBe(DARK.bg);
  expect(await bg(".sw-system .theme-light")).toBe(LIGHT.bg);
  expect(await bg(".sw-system .theme-dark")).toBe(DARK.bg);
});
