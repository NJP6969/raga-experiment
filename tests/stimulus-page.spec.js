// The stimulus check page loads each track when it is picked, decodes it, and keeps playing across switches.
const { test, expect } = require("@playwright/test");

test("@smoke every stimulus track on the check page loads, decodes and plays", async ({ page }) => {
  test.setTimeout(180_000);
  const errors = [];
  page.on("pageerror", e => errors.push(e.message));
  await page.goto("test.html");
  const tracks = page.locator("#tracks .tracks button");
  await expect(tracks).toHaveCount(4);
  await expect(page.locator("#play")).toBeEnabled({ timeout: 60_000 });   // the first track loads on its own
  await page.locator("#play").click();
  await expect(page.locator("#play")).toHaveText("Pause");
  for (let i = 0; i < 4; i++) {
    await tracks.nth(i).click();
    await expect(tracks.nth(i)).toHaveClass(/on/);
    await expect.poll(() => page.evaluate(k => !!buffers[k] && buffers[k].duration > 60, i), { timeout: 60_000 }).toBe(true);
    await expect(page.locator("#time")).not.toHaveText(/\/ 0:00$/);
  }
  await expect(page.locator("#play")).toHaveText("Pause");
  await expect(page.locator("#loading")).toBeHidden();
  expect(errors).toEqual([]);
});
