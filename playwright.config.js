const { defineConfig } = require("@playwright/test");
module.exports = defineConfig({
  testDir: "./tests/browser",
  fullyParallel: false,
  workers: 1,
  timeout: 30000,
  retries: 0,
  reporter: "list",
  use: {
    baseURL: "http://127.0.0.1:8091",
    viewport: { width: 1440, height: 1000 },
    headless: true,
    reducedMotion: "reduce",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    launchOptions: process.env.CHROMIUM_PATH
      ? {
          executablePath: process.env.CHROMIUM_PATH,
          args: [
            "--no-sandbox",
            "--no-zygote",
            "--disable-dev-shm-usage",
            "--use-gl=angle",
            "--use-angle=swiftshader",
            "--enable-unsafe-swiftshader",
          ],
        }
      : {},
  },
  webServer: {
    command: ".venv/bin/python tests/browser/server.py",
    url: "http://127.0.0.1:8091/health",
    reuseExistingServer: false,
    timeout: 30000,
  },
});
