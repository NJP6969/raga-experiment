// "About you" page (after consent): "Are you part of the Music Course?"
//   Yes -> full name and roll number, both required.   No -> roll number only, optional.
// A roll number, when given, must be exactly 10 digits.
const { test, expect, TASK, open, press, isTouch, acceptConsent } = require("./helpers");

const begin = page => page.locator("#start");
async function answerOthers(page) {                       // every field except the course question, name and roll number
  await page.selectOption("#famC", "3");
  await page.selectOption("#famH", "2");
  await page.check("#hear");
}
const course = (page, v) => page.getByRole("radio", { name: v === "yes" ? "Yes" : "No", exact: true });
const saved = page => page.evaluate(() => JSON.parse(localStorage.getItem("raga_state_v1") || "null"));

test.describe("intro page", () => {
  test.beforeEach(async ({ page }) => { await open(page, TASK, { clock: false }); await acceptConsent(page); });

  test("asks about the Music Course first; Begin waits for an answer", async ({ page }) => {
    await expect(page.getByRole("group", { name: "Are you part of the Music Course?" })).toBeVisible();
    await expect(page.locator("#pname")).toBeHidden();
    await expect(page.locator("#pid")).toBeHidden();
    await answerOthers(page);
    await expect(begin(page)).toBeDisabled();
  });

  test("Yes: full name and a 10-digit roll number are both required", async ({ page }) => {
    await course(page, "yes").check();
    await answerOthers(page);
    await expect(page.locator("#pname")).toBeVisible();
    await expect(page.locator("#pid")).toBeVisible();
    await expect(page.locator("label[for=pid]")).not.toContainText("optional");
    await expect(begin(page)).toBeDisabled();

    await page.fill("#pid", "2023102029");
    await expect(begin(page)).toBeDisabled();                          // name still missing
    await page.locator("#pname").focus(); await page.locator("#pname").blur();
    await expect(page.locator("#nameMsg")).toContainText("full name");
    await page.fill("#pname", "Priya Raman");
    await expect(begin(page)).toBeEnabled();

    await page.fill("#pid", "202310202");                              // 9 digits
    await page.locator("#pid").blur();
    await expect(page.locator("#pidMsg")).toHaveText("Roll number must be exactly 10 digits.");
    await expect(begin(page)).toBeDisabled();
    await page.fill("#pid", "");
    await expect(begin(page)).toBeDisabled();                          // required when Yes
  });

  test("roll number field keeps digits only and stops at 10", async ({ page }) => {
    await course(page, "yes").check();
    await page.locator("#pid").pressSequentially("20ab23-102 0299");
    await expect(page.locator("#pid")).toHaveValue("2023102029");
    await page.fill("#pid", "");
    await page.locator("#pid").pressSequentially("2023 102 029");   // pasted with spaces
    await expect(page.locator("#pid")).toHaveValue("2023102029");
    await expect(page.locator("#pidMsg")).not.toHaveClass(/err/);
  });

  test("No: only the roll number is shown, and it is optional", async ({ page }) => {
    await course(page, "no").check();
    await answerOthers(page);
    await expect(page.locator("#pname")).toBeHidden();
    await expect(page.locator("#pid")).toBeVisible();
    await expect(page.locator("label[for=pid]")).toContainText("optional");
    await expect(begin(page)).toBeEnabled();                           // empty is fine
    await page.fill("#pid", "12345");
    await page.locator("#pid").blur();
    await expect(begin(page)).toBeDisabled();                          // but if given, it must be 10 digits
    await expect(page.locator("#pidMsg")).toHaveText("Roll number must be exactly 10 digits.");
    await page.fill("#pid", "1234567890");
    await expect(begin(page)).toBeEnabled();
  });

  test("names must contain letters", async ({ page }) => {
    await course(page, "yes").check();
    await answerOthers(page);
    await page.fill("#pid", "2023102029");
    for (const bad of ["", "   ", "1234", "<b>x</b>", "A"]) {
      await page.fill("#pname", bad);
      await expect(begin(page), JSON.stringify(bad)).toBeDisabled();
    }
    for (const good of ["Priya Raman", "D'Souza", "Ravi K. Iyer", "ప్రియ రామన్"]) {
      await page.fill("#pname", good);
      await expect(begin(page), good).toBeEnabled();
    }
  });

  test("course member: name and roll number are recorded", async ({ page }, testInfo) => {
    await course(page, "yes").check();
    await page.fill("#pname", "  Priya   Raman ");
    await page.fill("#pid", "2023102029");
    await answerOthers(page);
    await press(page, begin(page), isTouch(testInfo));
    await expect.poll(() => saved(page)).not.toBeNull();
    const { P } = await saved(page);
    expect(P).toMatchObject({ id: "2023102029", musicCourse: 1, name: "Priya Raman" });
    expect(Date.now() - Date.parse(P.consentAt), "consent time recorded").toBeLessThan(60_000);
  });

  test("not in the course, no roll number: gets a unique anonymous ID", async ({ page }, testInfo) => {
    await course(page, "no").check();
    await answerOthers(page);
    await press(page, begin(page), isTouch(testInfo));
    await expect.poll(() => saved(page)).not.toBeNull();
    const { P } = await saved(page);
    expect(P.musicCourse).toBe(0);
    expect(P.name).toBe("");
    expect(P.id).toBe(`anon-${P.session}`);
  });
});
