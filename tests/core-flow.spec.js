// The experiment itself must keep working exactly as before: practice, five blocks of eight
// 9-digit lists in the Williams-design order, ratings, results table and the data files.
const { test, expect, TASK, isTouch, open, waitEnabled, advanceUntil, press, startSession, doPractice, doBlock, downloadCSV } = require("./helpers");

test.describe("core experiment flow", () => {
  test.setTimeout(240_000);

  test("full session: practice, 5 blocks, results and data files", async ({ page }, testInfo) => {
    const touch = isTouch(testInfo);
    await open(page, TASK);
    await startSession(page, touch);
    await doPractice(page, touch);
    await press(page, page.locator("#go"), touch);
    for (let k = 0; k < 5; k++) {
      await doBlock(page, touch, k);
      if (k < 4) await advanceUntil(page, page.getByRole("heading", { name: `Block ${k + 2} of 5` }));
    }
    await expect(page.getByRole("heading", { name: "Done, thank you" })).toBeVisible();
    await expect(page.locator("#saveStatus")).toContainText("Test mode");
    await expect(page.locator("table tr")).toHaveCount(6);              // header + 5 conditions

    const trials = await downloadCSV(page, "#d1");
    const recall = trials.filter(r => r.task === "recall");
    expect(recall).toHaveLength(40);
    expect(recall.every(r => r.list_length === "9" && /^[1-9]{9}$/.test(r.stimulus))).toBe(true);
    expect(recall.every(r => r.response === r.stimulus && r.n_correct_positions === "9")).toBe(true);
    expect(new Set(recall.map(r => r.condition))).toEqual(new Set(["A", "B", "C", "D", "E"]));
    expect(recall.map(r => r.condition).filter((c, i, a) => c !== a[i - 1]).join("")).toBe("ABECD");
    expect(recall.every(r => r.participant === "2023102029" && r.test_run === "1" && r.order === "ABECD")).toBe(true);
    expect(recall.every(r => r.music_course === "1" && r.full_name === "Test Student")).toBe(true);
    expect(trials.every(r => /^\d{4}-\d\d-\d\dT[\d:.]+Z$/.test(r.consent_time)), "consent time on every row").toBe(true);
    expect(recall.every(r => r.theme === "system" && r.theme_resolved === "light")).toBe(true);
    expect(recall[0].input).toBe(touch ? "keypad" : "keyboard");
    expect(recall[0].device).toBe(touch ? "touch" : "computer");
    const ratings = trials.filter(r => r.task === "rating");
    expect(ratings).toHaveLength(2 + 5 * 2 + 4);                        // baseline + alertness/mood per block + "how Indian" for 4 music blocks

    const blocks = await downloadCSV(page, "#d2");
    expect(blocks).toHaveLength(5);
    expect(blocks.map(b => b.condition).join("")).toBe("ABECD");
    expect(blocks.every(b => b.recall_prop_correct === "1" && b.music_course === "1" && b.full_name === "Test Student")).toBe(true);
  });

  test("reload mid-session offers to continue and restarts the interrupted block", async ({ page }, testInfo) => {
    const touch = isTouch(testInfo);
    await open(page, TASK);
    await startSession(page, touch);
    await doPractice(page, touch);
    await press(page, page.locator("#go"), touch);
    await doBlock(page, touch, 0);
    await advanceUntil(page, page.getByRole("heading", { name: "Block 2 of 5" }));
    page.on("dialog", d => d.accept());                                  // the "leave site?" guard
    await page.reload();
    await expect(page.getByRole("heading", { name: "Welcome back" })).toBeVisible();
    await expect(page.locator("#app")).toContainText("You completed 1 of 5 blocks");
    await press(page, page.locator("#cont"), touch);
    await expect(page.getByRole("heading", { name: "Choose a theme" })).toBeVisible();
    await press(page, page.locator("#go"), touch);
    await waitEnabled(page, page.locator("#ok"));
    await press(page, page.locator("#ok"), touch);
    await expect(page.getByRole("heading", { name: "Continuing" })).toBeVisible();
    await press(page, page.locator("#go"), touch);
    await expect(page.getByRole("heading", { name: "Block 2 of 5" })).toBeVisible();
  });
});
