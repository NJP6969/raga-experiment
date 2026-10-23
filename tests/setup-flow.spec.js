// Page order after the intro: Setup (theme, default System, with a live preview) -> volume -> practice ("testing").
const { test, expect, TASK, open, press, isTouch, fillIntro, waitEnabled, doList, advanceUntil, rate } = require("./helpers");

const heading = (page, name) => page.getByRole("heading", { name });
const themeRadio = (page, name) => page.getByRole("radio", { name: new RegExp(`^${name}`) });
const lumBody = page => page.evaluate(() => {
  const [r, g, b] = getComputedStyle(document.body).backgroundColor.match(/\d+/g).map(Number);
  return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
});

async function toThemePage(page, touch) {
  await fillIntro(page);
  await press(page, page.locator("#start"), touch);
  await expect(heading(page, "Choose a theme")).toBeVisible();
}

test.describe("setup flow", () => {
  test("intro -> theme -> volume -> practice, in that order", async ({ page }, testInfo) => {
    const touch = isTouch(testInfo);
    await open(page, TASK);
    await expect(heading(page, "Welcome")).toBeVisible();
    await toThemePage(page, touch);
    await press(page, page.locator("#go"), touch);
    await expect(heading(page, "Set your volume")).toBeVisible();
    await waitEnabled(page, page.locator("#ok"));
    await press(page, page.locator("#ok"), touch);
    await expect(heading(page, "The task: number lists")).toBeVisible();
  });

  test("theme page starts on System and the device setting is shown", async ({ page }, testInfo) => {
    await page.emulateMedia({ colorScheme: "dark" });
    await open(page, TASK, { clock: false });
    await toThemePage(page, isTouch(testInfo));
    await expect(themeRadio(page, "System")).toBeChecked();
    await expect(page.locator("#sysNow")).toHaveText("dark");
    await page.emulateMedia({ colorScheme: "light" });                 // follows the device live
    await expect(page.locator("#sysNow")).toHaveText("light");
    expect(await lumBody(page)).toBeGreaterThan(0.85);
  });

  test("choosing a theme applies straight away, with a preview of the task screens", async ({ page }, testInfo) => {
    const touch = isTouch(testInfo);
    await open(page, TASK, { clock: false });
    await toThemePage(page, touch);
    const preview = page.getByRole("img", { name: /Preview/ });
    await expect(preview).toBeVisible();
    await expect(preview).toContainText("7");                          // a digit, keypad and rating scale as in the task
    await themeRadio(page, "Dark").check();
    expect(await lumBody(page)).toBeLessThan(0.1);
    const previewBg = () => preview.evaluate(el => getComputedStyle(el).backgroundColor);
    const darkBg = await previewBg();
    await themeRadio(page, "Light").check();
    expect(await lumBody(page)).toBeGreaterThan(0.85);
    expect(await previewBg()).not.toBe(darkBg);
    await expect(themeRadio(page, "Light")).toBeChecked();
    await press(page, page.locator("#go"), touch);
    await expect(heading(page, "Set your volume")).toBeVisible();
    expect(await page.evaluate(() => localStorage.getItem("raga_theme"))).toBe("light");
  });

  test("theme is recorded with every data row", async ({ page }, testInfo) => {
    const touch = isTouch(testInfo);
    await open(page, TASK);
    await toThemePage(page, touch);
    await themeRadio(page, "Dark").check();
    await press(page, page.locator("#go"), touch);
    await waitEnabled(page, page.locator("#ok"));
    await press(page, page.locator("#ok"), touch);
    await press(page, page.locator("#go"), touch);                     // practice lists, then the baseline rating
    for (let i = 0; i < 2; i++) await doList(page, touch);
    await advanceUntil(page, page.locator("#next"));
    await rate(page, 3, touch);
    const st = await page.evaluate(() => JSON.parse(localStorage.getItem("raga_state_v1")));
    expect(st.rows.length).toBeGreaterThan(0);
    for (const r of st.rows) expect(r).toMatchObject({ theme: "dark", theme_resolved: "dark" });
  });

  test("a resumed session goes through the theme page again, with the saved choice selected", async ({ page }, testInfo) => {
    const touch = isTouch(testInfo);
    await open(page, TASK);
    await toThemePage(page, touch);
    await themeRadio(page, "Dark").check();
    await press(page, page.locator("#go"), touch);
    await expect(heading(page, "Set your volume")).toBeVisible();
    page.on("dialog", d => d.accept());
    await page.reload();
    await expect(heading(page, "Welcome back")).toBeVisible();
    await press(page, page.locator("#cont"), touch);
    await expect(heading(page, "Choose a theme")).toBeVisible();
    await expect(themeRadio(page, "Dark")).toBeChecked();
    await press(page, page.locator("#go"), touch);
    await expect(heading(page, "Set your volume")).toBeVisible();
  });
});
