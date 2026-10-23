// Information and consent: six short steps (welcome, what you'll do, before you start, your data, your choices,
// consent), each fitting on one screen, with Back and Next. Nothing is saved before the participant agrees;
// declining ends politely.
const { test, expect, TASK, open, press, isTouch, startSession, advanceUntil } = require("./helpers");

const STEPS = ["Welcome", "What you'll do", "Before you start", "Your data", "Your choices", "Consent"];
const heading = (page, name) => page.getByRole("heading", { name, exact: true });
const boxes = page => page.locator("#consent input[type=checkbox]");
const savedState = page => page.evaluate(() => localStorage.getItem("raga_state_v1"));
const toConsent = async page => { for (let i = 1; i < STEPS.length; i++) await page.locator("#infoNext").click(); };

test.describe("information and consent", () => {
  test.beforeEach(async ({ page }) => { await open(page, TASK, { clock: false }); });

  test("six short steps, in order, each fitting on one screen", async ({ page }, testInfo) => {
    const touch = isTouch(testInfo);
    for (const [i, name] of STEPS.entries()) {
      await expect(heading(page, name)).toBeVisible();
      await expect(page.locator(".step-count")).toHaveText(`Step ${i + 1} of ${STEPS.length}`);
      await expect(page.locator("#infoBack")).toHaveCount(i === 0 ? 0 : 1);   // no Back on the first step
      await expect(page.locator("#progress")).toBeVisible({ visible: i === 0 }); // the bar only on the first page of the phase
      expect(await page.evaluate(() => window.scrollY), `${name} opens at its top`).toBe(0);
      const button = page.locator(i < STEPS.length - 1 ? "#infoNext" : "#agree");
      await expect(button, `${name}: button visible without scrolling`).toBeInViewport({ ratio: 1 });
      if (i < STEPS.length - 1) await press(page, button, touch);
    }
  });

  test("Back returns to the previous step", async ({ page }) => {
    await toConsent(page);
    for (const name of [...STEPS].reverse().slice(1)) {
      await page.locator("#infoBack").click();
      await expect(heading(page, name)).toBeVisible();
    }
    await expect(page.locator("#infoBack")).toHaveCount(0);
  });

  test("covers the study, the steps, the instructions and data privacy", async ({ page }) => {
    let text = "";
    for (let i = 0; i < STEPS.length; i++) {
      text += await page.locator("#app").innerText();
      if (i < STEPS.length - 1) await page.locator("#infoNext").click();
    }
    for (const t of ["About 18 minutes", "headphones", "within 6 hours", "What we record", "DataPipe",
                     "removed before the data are analysed or shared", "Stop at any time", "course instructor"])
      expect(text, t).toContain(t);
    await expect(page.locator(".steps li")).toHaveCount(0);            // the steps list was on step 2, not here
    expect(await savedState(page)).toBeNull();
  });

  test("continuing needs all three statements ticked", async ({ page }) => {
    await toConsent(page);
    const agree = page.locator("#agree");
    await expect(boxes(page)).toHaveCount(3);
    await expect(agree).toBeDisabled();
    await page.getByText("I have read and understood").click();          // the whole row is the tap target
    await boxes(page).nth(1).check();
    await expect(agree).toBeDisabled();
    await boxes(page).nth(2).check();
    await expect(agree).toBeEnabled();
    await boxes(page).nth(0).uncheck();
    await expect(agree).toBeDisabled();
    await boxes(page).nth(0).check();
    await agree.click();
    await expect(heading(page, "About you")).toBeVisible();
    expect(await savedState(page)).toBeNull();                          // still nothing saved until Begin
  });

  test("declining records nothing, and the information can be read again", async ({ page }) => {
    await toConsent(page);
    await page.locator("#decline").click();
    await expect(heading(page, "Thank you for your time")).toBeVisible();
    await expect(page.locator("#app")).toContainText("None of your answers have been recorded");
    expect(await savedState(page)).toBeNull();
    await page.getByRole("button", { name: "Back to the information" }).click();
    await expect(heading(page, "Welcome")).toBeVisible();
    await toConsent(page);
    await expect(page.locator("#agree")).toBeDisabled();                 // ticks start empty again
  });
});

test("header and footer frame the information pages, and step aside during the task", async ({ page }, testInfo) => {
  const touch = isTouch(testInfo);
  await open(page, TASK);
  await expect(page.locator(".site-header")).toBeVisible();
  await expect(page.locator(".site-footer")).toBeVisible();
  await startSession(page, touch);                                      // ends on the practice instructions
  await expect(page.locator(".site-header")).toBeVisible();
  await press(page, page.locator("#go"), touch);
  await advanceUntil(page, page.locator("#app .big"), { step: 250 });  // a digit on screen
  await expect(page.locator(".site-header")).toBeHidden();
  await expect(page.locator(".site-footer")).toBeHidden();
});
