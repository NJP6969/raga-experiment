// First page: information about the study, what participants will do, instructions, data privacy and consent.
// Nothing is saved before the participant agrees; declining ends politely.
const { test, expect, TASK, open, press, isTouch, startSession, advanceUntil } = require("./helpers");

const heading = (page, name) => page.getByRole("heading", { name, exact: true });
const boxes = page => page.locator("#consent input[type=checkbox]");
const savedState = page => page.evaluate(() => localStorage.getItem("raga_state_v1"));

test.describe("information and consent", () => {
  test.beforeEach(async ({ page }) => { await open(page, TASK, { clock: false }); });

  test("explains the study, the steps, the instructions and data privacy before asking", async ({ page }) => {
    for (const h of ["Welcome", "About this study", "What you'll do", "Before you start", "Your data and privacy", "Consent"])
      await expect(heading(page, h)).toBeVisible();
    await expect(page.locator(".steps li")).toHaveCount(5);
    const app = page.locator("#app");
    for (const text of ["About 18 minutes", "headphones", "within 6 hours", "What we record", "DataPipe",
                        "removed before the data are analysed or shared", "stop at any time", "course instructor"])
      await expect(app).toContainText(text);
    await expect(page.locator("#progLabel")).toHaveText("Intro");
    expect(await savedState(page)).toBeNull();
  });

  test("continuing needs all three statements ticked", async ({ page }) => {
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
    await page.locator("#decline").click();
    await expect(heading(page, "Thank you for your time")).toBeVisible();
    await expect(page.locator("#app")).toContainText("None of your answers have been recorded");
    expect(await savedState(page)).toBeNull();
    await page.getByRole("button", { name: "Back to the information" }).click();
    await expect(heading(page, "Welcome")).toBeVisible();
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
