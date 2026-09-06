const { test, expect } = require("@playwright/test");

for (const notified of [true, false]) {
  test(`Mini App reports Telegram delivery ${notified ? "success" : "failure"} without an email form`, async ({
    page,
    request,
  }) => {
    await page.route("https://telegram.org/**", (route) =>
      route.fulfill({ contentType: "application/javascript", body: "" }),
    );
    const meta = await (await request.get("/api/bootstrap")).json();
    const snapshot = await (await request.get("/api/session")).json();
    snapshot.user.trial_used = false;
    snapshot.user.trial_status = null;
    snapshot.catalog.trial.enabled = true;
    snapshot.configs = [];
    await page.route("**/api/bootstrap", (route) =>
      route.fulfill({ json: { ...meta, demo: false } }),
    );
    await page.route("**/api/session", (route) =>
      route.fulfill({ json: snapshot }),
    );
    await page.route("**/api/trial", (route) => {
      expect(route.request().postData()).toBeNull();
      return route.fulfill({
        status: 201,
        json: {
          ...snapshot,
          notified,
          user: { ...snapshot.user, trial_used: true },
          configs: [
            {
              id: "trial_delivery_fixture",
              plan_name: "تست یک‌روزه پینگینو",
              category: "regular",
              traffic_gb: 1,
              days: 1,
              active: true,
              is_trial: true,
              renewable: true,
              expires_at: new Date(Date.now() + 86400000).toISOString(),
              config_link: "https://example.invalid/sub/delivery-test",
            },
          ],
        },
      });
    });
    await page.goto("/");
    await page.locator(".hero [data-action='trial']").click();
    await expect(page.locator("input[type=email]")).toHaveCount(0);
    await page
      .getByRole("button", { name: "دریافت تست یک‌روزه", exact: true })
      .click();
    await expect(
      page.getByRole("heading", { name: "تست یک‌روزه پینگینو", exact: true }),
    ).toBeVisible();
    if (notified) {
      await expect(page.getByRole("status")).toContainText(
        "لینک کانفیگ داخل تلگرام برات ارسال شد",
      );
      await expect(page.locator(".toast.error")).toHaveCount(0);
    } else {
      await expect(page.getByRole("status")).toContainText(
        "ارسال پیام تلگرام ناموفق بود",
      );
      await expect(page.getByRole("status")).toContainText("/myconfigs");
      await expect(page.locator(".toast.error")).toBeVisible();
    }
  });
}
