const { test, expect } = require("@playwright/test");
const { default: AxeBuilder } = require("@axe-core/playwright");

test.beforeEach(async ({ page }) => {
  // Browser tests do not depend on Telegram's CDN or a real Telegram account.
  await page.route("https://telegram.org/**", (route) =>
    route.fulfill({ contentType: "application/javascript", body: "" }),
  );
});

async function openHome(page) {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "خونهٔ پینگینویی تو" }),
  ).toBeVisible();
}
async function go(page, name) {
  await page.locator(`.sidebar [data-page="${name}"]`).first().click();
}

test("Persian storefront, real category filtering and responsive layouts", async ({
  page,
}) => {
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await openHome(page);
  await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
  await expect(page.locator(".plan-card")).toHaveCount(3);
  await expect(
    page.getByRole("heading", { name: "پینگینو پلاس" }),
  ).toBeVisible();
  await page.locator('.segmented [data-category="gaming"]').click();
  await expect(
    page.getByRole("heading", { name: "گیمینگ پلاس" }),
  ).toBeVisible();
  await expect(page.getByRole("heading", { name: "پینگینو پلاس" })).toHaveCount(
    0,
  );
  for (const width of [1440, 1024, 768, 390, 320]) {
    await page.setViewportSize({ width, height: 850 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBeTruthy();
  }
  await expect(page.locator(".mobile-nav")).toBeVisible();
  await page.locator('.mobile-nav [data-page="configs"]').click();
  await expect(
    page.getByRole("heading", { name: "کانفیگ‌های من", exact: true }),
  ).toBeVisible();
  expect(errors).toEqual([]);
});

test("admin saves Persian prices and quotas; existing invoices keep old terms", async ({
  page,
  request,
}) => {
  const before = (await (await request.get("/api/session")).json()).catalog
    .plans.regular_plus;
  const old = (
    await (
      await request.post("/api/orders", { data: { plan_id: "regular_plus" } })
    ).json()
  ).order;
  try {
    await openHome(page);
    await go(page, "admin");
    await page
      .locator('[data-action="edit-plan"][data-id="regular_plus"]')
      .click();
    await page.getByLabel("قیمت (تومان)", { exact: true }).fill("۱۸۸٬۰۰۰");
    await page.getByLabel("حجم (گیگابایت)", { exact: true }).fill("۸۸");
    await page.getByRole("button", { name: "ذخیرهٔ تغییرات" }).click();
    await expect(page.getByRole("dialog")).not.toBeVisible();
    await page.reload();
    await expect(
      page.locator("tr").filter({ hasText: "پینگینو پلاس" }),
    ).toContainText("۱۸۸٬۰۰۰");
    await expect(
      page.locator("tr").filter({ hasText: "پینگینو پلاس" }),
    ).toContainText("۸۸ گیگ");
    await go(page, "home");
    const card = page
      .locator(".plan-card")
      .filter({ has: page.getByRole("heading", { name: "پینگینو پلاس" }) });
    await expect(card).toContainText("۱۸۸٬۰۰۰");
    await expect(card.locator(".plan-amount")).toContainText("۸۸");
    const invoice = (await (await request.get(`/api/orders/${old.id}`)).json())
      .order;
    expect(invoice.price).toBe(before.price);
    expect(invoice.traffic_gb).toBe(before.traffic_gb);
  } finally {
    await request.patch("/api/admin/plans/regular_plus", {
      data: { price: before.price, traffic_gb: before.traffic_gb },
    });
  }
});

test("full demo purchase: invoice, receipt, admin review, approval and config delivery", async ({
  page,
}) => {
  await openHome(page);
  await page.locator('.segmented [data-category="gaming"]').click();
  await page
    .locator('[data-action="select-plan"][data-id="gaming_light"]')
    .click();
  const orderResponse = page.waitForResponse(
    (r) => r.url().endsWith("/api/orders") && r.request().method() === "POST",
  );
  await page.getByRole("button", { name: "ثبت سفارش و ادامه" }).click();
  const order = (await (await orderResponse).json()).order;
  await expect(page.locator(".bank-card")).toContainText(
    "نمایشی — پرداخت نکنید",
  );
  await page.getByRole("button", { name: "ثبت رسید آزمایشی" }).click();
  await expect(page.locator("tr").filter({ hasText: order.id })).toContainText(
    "در انتظار تأیید",
  );
  await go(page, "admin");
  await page.locator('[data-action="admin-tab"][data-tab="orders"]').click();
  await page
    .locator("tr")
    .filter({ hasText: order.id })
    .getByRole("button", { name: "بررسی سفارش" })
    .click();
  await page.getByRole("button", { name: "مشاهدهٔ تصویر رسید" }).click();
  await expect(page.locator(".receipt-preview")).toBeVisible();
  await page.getByRole("button", { name: "تأیید و فعال‌سازی" }).click();
  await expect(page.getByRole("dialog")).not.toBeVisible();
  await expect(page.locator("tr").filter({ hasText: order.id })).toContainText(
    "تأیید شده",
  );
  await go(page, "configs");
  const cfg = page
    .locator(".config-card")
    .filter({ hasText: "گیمینگ استارتر" })
    .first();
  await expect(cfg).toContainText("فعال");
  await cfg.getByRole("button", { name: "مشاهده و کپی لینک" }).click();
  await expect(page.locator(".copy-field")).toContainText(
    "https://example.invalid/",
  );
});

test("one-day trial survives reload and cannot be claimed twice", async ({
  page,
  request,
}) => {
  await openHome(page);
  await page.locator('.hero [data-action="trial"]').click();
  await expect(page.getByRole("dialog")).toContainText("۲۴ ساعت");
  await page
    .getByRole("button", { name: "دریافت تست یک‌روزه", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "تست یک‌روزه پینگینو", exact: true }),
  ).toBeVisible();
  await page.reload();
  await page.locator('.sidebar [data-action="trial"]').click();
  await expect(page.getByRole("dialog")).toContainText(
    "اولین هدیه‌ات رو گرفتی.",
  );
  const response = await request.post("/api/trial");
  expect(response.status()).toBe(409);
  const data = await (await request.get("/api/session")).json();
  expect(data.configs.filter((c) => c.is_trial)).toHaveLength(1);
});

test("membership gate waits for successful server verification", async ({
  page,
  request,
}) => {
  const snapshot = await (await request.get("/api/session")).json();
  let checks = 0;
  await page.route("**/api/bootstrap", (route) =>
    route.fulfill({
      json: {
        demo: false,
        configured: true,
        channel_url: "https://t.me/pingino_org",
        bot_username: "pinginoo_test_bot",
        support_username: "",
      },
    }),
  );
  await page.route("**/api/session", (route) =>
    route.fulfill({
      status: 403,
      json: { code: "membership_required", message: "اول عضو کانال شو." },
    }),
  );
  await page.route("**/api/membership/check", (route) => {
    checks++;
    return route.fulfill(
      checks === 1
        ? {
            status: 403,
            json: { code: "membership_required", message: "هنوز عضو نیستی." },
          }
        : { json: { joined: true, ...snapshot } },
    );
  });
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "اول به خانوادهٔ پینگینو بپیوند." }),
  ).toBeVisible();
  await expect(page.locator(".plan-card")).toHaveCount(0);
  await page.getByRole("button", { name: "عضو شدم؛ بررسی کن" }).click();
  await expect(
    page.getByRole("heading", { name: "اول به خانوادهٔ پینگینو بپیوند." }),
  ).toBeVisible();
  await page.getByRole("button", { name: "عضو شدم؛ بررسی کن" }).click();
  await expect(
    page.getByRole("heading", { name: "خونهٔ پینگینویی تو" }),
  ).toBeVisible();
  expect(checks).toBe(2);
});

test("guide, FAQ, keyboard dialog close and history search work on mobile", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await openHome(page);
  await page.locator('.bottom-panels [data-page="help"]').click();
  await page.getByRole("button", { name: "آیفون", exact: true }).click();
  await expect(page.locator("#guide-content")).toContainText("Streisand");
  await page.getByText("باید عضو کانال بمونم؟", { exact: true }).click();
  await expect(page.locator("details[open]")).toContainText("بله.");
  await page.locator('.mobile-nav [data-page="history"]').click();
  await page
    .getByRole("textbox", { name: "جستجوی سفارش" })
    .fill("nothing matches");
  await expect(
    page.getByRole("heading", { name: "سفارشی پیدا نشد." }),
  ).toBeVisible();
  await page.getByRole("textbox", { name: "جستجوی سفارش" }).fill("");
  await page.locator('tr [data-action="order"]').first().click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).not.toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
});

test("user-provided names are text, never executable HTML", async ({
  page,
  request,
}) => {
  const snapshot = await (await request.get("/api/session")).json();
  const attack = '<img src=x onerror="window.hacked=true">';
  snapshot.user.first_name = attack;
  snapshot.catalog.plans.regular_plus.name = attack;
  await page.route("**/api/session", (route) =>
    route.fulfill({ json: snapshot }),
  );
  await openHome(page);
  await expect(page.locator(".sidebar-profile strong")).toHaveText(attack);
  expect(await page.locator('img[src="x"]').count()).toBe(0);
  expect(await page.evaluate(() => window.hacked)).toBeUndefined();
});

test("home has no WCAG A/AA accessibility violations", async ({ page }) => {
  await openHome(page);
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
    .analyze();
  expect(
    results.violations.map((v) => ({
      id: v.id,
      nodes: v.nodes.map((n) => ({
        target: n.target,
        summary: n.failureSummary,
      })),
    })),
  ).toEqual([]);
});
