// Browser tests for the Music and Memory Task.
// Every test runs on desktop, laptop, iPad (portrait and landscape) and phones (Android and iPhone sizes).
// Locally these all use Chromium with each device's screen, touch and user agent.
// With PW_WEBKIT=1 (set in CI) the iPhone, iPad and Mac Safari projects also run on the real WebKit engine.
// With BASE_URL set, the tests run against that site (e.g. the live GitHub Pages URL) instead of a local server.
const { defineConfig, devices } = require("@playwright/test");

const PORT = +process.env.PORT || 4173;
const BASE_URL = process.env.BASE_URL || `http://127.0.0.1:${PORT}/`;
const CI = !!process.env.CI;
const chromium = d => ({ ...d, browserName: "chromium", defaultBrowserType: "chromium" });

const projects = [
  { name: "desktop",        use: { ...devices["Desktop Chrome"], viewport: { width: 1920, height: 1080 } } },
  { name: "laptop",         use: { ...devices["Desktop Chrome"], viewport: { width: 1366, height: 768 } } },
  { name: "ipad",           use: chromium(devices["iPad (gen 7)"]) },
  { name: "ipad-landscape", use: chromium(devices["iPad Pro 11 landscape"]) },
  { name: "mobile-android", use: devices["Pixel 7"] },
  { name: "mobile-iphone",  use: chromium(devices["iPhone 14"]) }
];
if (process.env.PW_WEBKIT) {
  projects.push(
    { name: "webkit-iphone",  use: devices["iPhone 14"] },
    { name: "webkit-ipad",    use: devices["iPad (gen 7)"] },
    { name: "webkit-desktop", use: { ...devices["Desktop Safari"], viewport: { width: 1440, height: 900 } } }
  );
}

module.exports = defineConfig({
  testDir: "tests",
  timeout: 60_000,
  expect: { timeout: 10_000 },
  fullyParallel: true,
  forbidOnly: CI,
  retries: CI ? 1 : 0,
  workers: CI ? 2 : undefined,
  reporter: CI ? [["list"], ["html", { open: "never" }], ["github"]] : [["list"]],
  use: {
    baseURL: BASE_URL,
    trace: "retain-on-failure",
    screenshot: "only-on-failure"
  },
  projects,
  webServer: process.env.BASE_URL ? undefined : {
    command: "node tests/server.js",
    url: BASE_URL,
    reuseExistingServer: !CI,
    env: { PORT: String(PORT) }
  }
});
