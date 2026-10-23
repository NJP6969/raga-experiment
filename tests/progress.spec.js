// Top progress bar: shown only on the first page of each phase (intro, setup, practice, questions
// before the task, the "about the task" page before each block, the questions after each block, the end),
// hidden everywhere else, and always showing how much of the whole session is done.
const { test, expect, TASK, open, press, isTouch, fillIntro, waitEnabled, advanceUntil, enterDigits, rate } = require("./helpers");

const bar = async page => {
  const box = page.locator("#progress");
  if (!(await box.isVisible())) return null;
  return { label: (await page.locator("#progLabel").textContent()).trim(), pct: +(await box.getByRole("progressbar").getAttribute("aria-valuenow")) };
};
const heading = (page, name) => page.getByRole("heading", { name });

async function answerList(page, touch) {               // presentation and answer screens never show the bar
  await advanceUntil(page, page.locator("#app .big"), { step: 250 });
  expect(await bar(page)).toBeNull();
  await advanceUntil(page, page.locator("#slots"), { step: 2000 });
  expect(await bar(page)).toBeNull();
  await enterDigits(page, "123456789", touch);
}

test("bar shows only on the first page of each phase, and only goes up", async ({ page }, testInfo) => {
  test.setTimeout(240_000);
  const touch = isTouch(testInfo);
  const seen = [];
  const expectBar = async label => { const b = await bar(page); expect(b, `bar on "${label}" page`).not.toBeNull(); expect(b.label).toBe(label); seen.push(b); };

  await open(page, TASK);
  await expectBar("Intro");
  await fillIntro(page);
  await press(page, page.locator("#start"), touch);
  await expect(heading(page, "Choose a theme")).toBeVisible();
  await expectBar("Setup");
  await press(page, page.locator("#go"), touch);
  await expect(heading(page, "Set your volume")).toBeVisible();
  expect(await bar(page)).toBeNull();                                   // second page of setup
  await waitEnabled(page, page.locator("#ok"));
  await press(page, page.locator("#ok"), touch);
  await expect(heading(page, "The task: number lists")).toBeVisible();
  await expectBar("Practice");
  await press(page, page.locator("#go"), touch);
  for (let i = 0; i < 2; i++) await answerList(page, touch);
  await advanceUntil(page, page.locator("#next"));
  await expectBar("Questions before the task");
  await rate(page, 3, touch);
  await expect(heading(page, "Ready")).toBeVisible();
  await expectBar("About the task");
  await press(page, page.locator("#go"), touch);

  for (let k = 0; k < 5; k++) {
    await expect(heading(page, `Block ${k + 1} of 5`)).toBeVisible();
    await expectBar(`Block ${k + 1} of 5`);
    await waitEnabled(page, page.locator("#go"));
    await press(page, page.locator("#go"), touch);
    await page.clock.runFor(1000);
    expect(await bar(page)).toBeNull();                                 // lead-in
    for (let i = 0; i < 8; i++) await answerList(page, touch);
    await advanceUntil(page, page.locator("#next"));
    await expectBar(`Questions after block ${k + 1}`);
    await rate(page, 4, touch);
    if (k < 4) {
      await page.clock.runFor(500);
      expect(await bar(page)).toBeNull();                               // rest
      await advanceUntil(page, heading(page, `Block ${k + 2} of 5`));
    }
  }
  await expect(heading(page, "Done, thank you")).toBeVisible();
  await expectBar("Finished");

  const pcts = seen.map(s => s.pct);
  expect(pcts[0]).toBe(0);
  expect(pcts[pcts.length - 1]).toBe(100);
  for (let i = 1; i < pcts.length; i++) expect(pcts[i], `${seen[i].label} after ${seen[i - 1].label}`).toBeGreaterThan(pcts[i - 1]);
  await expect(page.locator("#progLabel ~ #progPct, #progPct")).toHaveText("100% done");
});

test("a resumed session's bar continues from where it was, it never drops back", async ({ page }, testInfo) => {
  const touch = isTouch(testInfo);
  const st = { nextBlock: 2, practiceDone: true, baselineDone: true, finished: false, savedAt: Date.now(), fast: true,
    P: { id: "2023102029", name: "Test Student", musicCourse: 1, session: "abcd1234", seed: 1, row: 0, order: "ABECD".split(""), orderSource: "url", resumes: 0, device: "computer", famC: 3, famH: 2, training: 0 },
    rows: [], blockSummaries: [] };
  await page.addInitScript(s => { if (!sessionStorage.getItem("seeded")) { localStorage.setItem("raga_state_v1", JSON.stringify(s)); sessionStorage.setItem("seeded", "1"); } }, st);
  await open(page, TASK);
  await expect(heading(page, "Welcome back")).toBeVisible();
  const welcome = await bar(page);
  expect(welcome.label).toBe("Welcome back");
  expect(welcome.pct).toBeGreaterThan(40);                              // 2 of 5 blocks done
  await press(page, page.locator("#cont"), touch);
  await expect(heading(page, "Choose a theme")).toBeVisible();
  expect((await bar(page)).pct).toBe(welcome.pct);                      // not back to the setup value
  await press(page, page.locator("#go"), touch);
  await waitEnabled(page, page.locator("#ok"));
  await press(page, page.locator("#ok"), touch);
  await expect(heading(page, "Continuing")).toBeVisible();
  expect((await bar(page)).pct).toBe(welcome.pct);
  await press(page, page.locator("#go"), touch);
  await expect(heading(page, "Block 3 of 5")).toBeVisible();
  expect((await bar(page)).pct).toBe(welcome.pct);
});
