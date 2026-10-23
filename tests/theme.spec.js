// Theme: System (default, follows the device), Light or Dark; one simple colour scheme for each.
const { test, expect, TASK } = require("./helpers");

const TOKENS = ["bg", "card", "fg", "heading", "muted", "line-strong", "accent", "accent-hover", "accent-fg", "accent-soft", "ok", "bad", "warn-bg", "warn-fg"];
const rgb = c => c.startsWith("#") ? [1, 3, 5].map(i => parseInt(c.slice(i, i + 2), 16)) : c.match(/\d+(\.\d+)?/g).slice(0, 3).map(Number);
const lum = c => { const [r, g, b] = rgb(c).map(v => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; }); return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
const contrast = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05); };
const tokens = page => page.evaluate(names => {
  const cs = getComputedStyle(document.documentElement);
  return Object.fromEntries(names.map(n => [n, cs.getPropertyValue("--" + n).trim()]));
}, TOKENS);
const bodyBg = page => page.evaluate(() => getComputedStyle(document.body).backgroundColor);
const choice = page => page.evaluate(() => [document.documentElement.getAttribute("data-theme-choice"), document.documentElement.getAttribute("data-theme")]);

test.describe("theme", () => {
  test("defaults to System and follows the device setting, live", async ({ page }) => {
    await page.emulateMedia({ colorScheme: "dark" });
    await page.goto(TASK);
    expect(await choice(page)).toEqual(["system", null]);
    expect(lum(await bodyBg(page))).toBeLessThan(0.05);
    await page.emulateMedia({ colorScheme: "light" });
    expect(lum(await bodyBg(page))).toBeGreaterThan(0.85);
    expect(await page.evaluate(() => Theme.resolved())).toBe("light");
  });

  test("Light and Dark override the device and are remembered across reloads and pages", async ({ page }) => {
    await page.emulateMedia({ colorScheme: "light" });
    await page.goto("test.html");
    await page.getByRole("button", { name: "Dark", exact: true }).click();
    expect(await choice(page)).toEqual(["dark", "dark"]);
    expect(lum(await bodyBg(page))).toBeLessThan(0.05);
    await page.reload();
    expect(await choice(page)).toEqual(["dark", "dark"]);
    await page.goto(TASK);                                              // same choice on the task page
    expect(lum(await bodyBg(page))).toBeLessThan(0.05);
    await page.emulateMedia({ colorScheme: "dark" });
    await page.evaluate(() => Theme.set("light"));
    expect(lum(await bodyBg(page))).toBeGreaterThan(0.85);
  });

  test("stimulus check page has a theme switcher that shows the active choice", async ({ page }) => {
    await page.goto("test.html");
    const group = page.getByRole("group", { name: "Theme" });
    await expect(group.getByRole("button", { name: "System" })).toHaveAttribute("aria-pressed", "true");
    await group.getByRole("button", { name: "Light" }).click();
    await expect(group.getByRole("button", { name: "Light" })).toHaveAttribute("aria-pressed", "true");
    await expect(group.getByRole("button", { name: "System" })).toHaveAttribute("aria-pressed", "false");
    await group.getByRole("button", { name: "System" }).click();
    expect(await choice(page)).toEqual(["system", null]);
  });

  test("an unknown saved value falls back to System", async ({ page }) => {
    await page.addInitScript(() => localStorage.setItem("raga_theme", "purple"));
    await page.goto(TASK);
    expect(await choice(page)).toEqual(["system", null]);
  });

  test("phone browser bar colour (theme-color) matches the page", async ({ page }) => {
    await page.goto(TASK);
    for (const t of ["dark", "light"]) {
      await page.evaluate(x => Theme.set(x), t);
      const [meta, bg] = await page.evaluate(() => [document.querySelector('meta[name="theme-color"]').content, getComputedStyle(document.documentElement).getPropertyValue("--bg").trim()]);
      expect(meta).toBe(bg);
    }
  });

  for (const t of ["light", "dark"]) {
    test(`${t} colours are readable (WCAG AA contrast)`, async ({ page }) => {
      await page.goto(TASK);
      await page.evaluate(x => Theme.set(x), t);
      const c = await tokens(page);
      for (const [fg, bg] of [["fg", "bg"], ["fg", "card"], ["muted", "bg"], ["muted", "card"], ["accent-fg", "accent"], ["accent", "card"],
                              ["ok", "card"], ["bad", "card"], ["warn-fg", "warn-bg"], ["fg", "accent-soft"],
                              ["heading", "bg"], ["heading", "card"], ["accent-fg", "accent-hover"]])
        expect(contrast(c[fg], c[bg]), `${fg} on ${bg}`).toBeGreaterThanOrEqual(4.5);
      expect(contrast(c["line-strong"], c.card), "input borders").toBeGreaterThanOrEqual(3);
      expect(contrast(c["line-strong"], c.bg), "key borders on the page background").toBeGreaterThanOrEqual(3);
      expect(t === "dark" ? lum(c.bg) < 0.05 : lum(c.bg) > 0.85).toBe(true);
    });
  }
});
