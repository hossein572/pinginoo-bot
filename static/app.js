/* Pinginoo Mini App. No secrets, identity or pricing authority lives in the browser. */
"use strict";

const icons = {
  home: '<path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1Z"/>',
  globe:
    '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a18 18 0 0 1 0 18 18 18 0 0 1 0-18Z"/>',
  game: '<path d="M7 7h10c3 0 4 3 4.6 7.5s-1 6-3 4l-3-2.5H8.4l-3 2.5c-2 2-3.5.5-3-4S4 7 7 7Z"/><path d="M7 10v5m-2.5-2.5h5M16 11h.01M18 14h.01M9 7l1-3h4l1 3"/>',
  box: '<path d="m12 3 9 5-9 5-9-5 9-5Zm9 5v10l-9 5-9-5V8m9 5v10M7.5 5.5l9 5V15"/>',
  receipt:
    '<path d="m5 3 2 1 2-1 3 1 3-1 2 1 2-1v18l-2-1-2 1-3-1-3 1-2-1-2 1V3Z"/><path d="M8 8h8M8 12h8M8 16h4"/>',
  book: '<path d="M12 5c-3-2-6-2-10-1v15c4-1 7-1 10 1 3-2 6-2 10-1V4c-4-1-7-1-10 1Zm0 0v15M5 8h3m-3 4h3m8-4h3m-3 4h3"/>',
  headset:
    '<path d="M3 13v-2a9 9 0 0 1 18 0v2M3 12h3v7H4a2 2 0 0 1-2-2v-3a2 2 0 0 1 1-2Zm18 0h-3v7h2a2 2 0 0 0 2-2v-3a2 2 0 0 0-1-2Zm-2 7c0 3-3 3-7 3"/>',
  settings:
    '<path d="m9 3-1 3-3 1v4l-2 2 2 3 3 1 1 4h6l1-4 3-1 2-3-2-2V7l-3-1-1-3H9Z"/><circle cx="12" cy="12" r="3"/>',
  arrow: '<path d="M19 12H5m6-6-6 6 6 6"/>',
  upLeft: '<path d="M18 18 6 6m0 10V6h10"/>',
  chevron: '<path d="m15 6-6 6 6 6"/>',
  shield:
    '<path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6l8-3Z"/><path d="m8 12 3 3 5-6"/>',
  check: '<path d="m5 12 4 4L19 6"/>',
  checkCircle: '<circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/>',
  plus: '<path d="M12 4v16M4 12h16"/>',
  close: '<path d="m6 6 12 12M6 18 18 6"/>',
  telegram:
    '<path d="m22 3-4 18-6-5-4 3 1-6L2 10 22 3Z"/><path d="m9 13 9-7-6 10"/>',
  bell: '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9ZM10 21h4"/>',
  moon: '<path d="M21 13a9 9 0 1 1-10-10 7 7 0 0 0 10 10Z"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1 1m12 12 1 1M5 19l1-1M18 6l1-1"/>',
  refresh:
    '<path d="M20 7v5h-5M4 17v-5h5M6 6a8 8 0 0 1 13 3M5 15a8 8 0 0 0 13 3"/>',
  gift: '<path d="M3 8h18v4H3V8Zm2 4v9h14v-9M12 8v13"/><path d="M12 8c-8 0-8-7-3-5 2 1 3 5 3 5Zm0 0c8 0 8-7 3-5-2 1-3 5-3 5Z"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  zap: '<path d="m13 2-9 12h7l-1 8 10-13h-8l1-7Z"/>',
  devices:
    '<rect x="3" y="3" width="16" height="12" rx="2"/><path d="M7 20h6m-3-5v5"/><rect x="15" y="10" width="6" height="11" rx="1"/>',
  users:
    '<circle cx="9" cy="8" r="4"/><path d="M2 21v-2a7 7 0 0 1 14 0v2M16 4a4 4 0 0 1 0 8m3 3a6 6 0 0 1 3 6"/>',
  chart: '<path d="M4 3v18h17M8 16v-4m5 4V7m5 9V4"/>',
  wallet:
    '<rect x="3" y="5" width="18" height="15" rx="3"/><path d="M3 8V5a2 2 0 0 1 2-2h12v2m4 6h-6v5h6M17 13.5h.01"/>',
  edit: '<path d="m15 4 5 5M4 20l1-5L17 3l4 4L9 19l-5 1Zm8 0h9"/>',
  copy: '<rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15H3V3h12v2"/>',
  calendar:
    '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M7 3v4m10-4v4M3 11h18m-14 4h2m4 0h2m-8 3h2"/>',
  search: '<circle cx="10.5" cy="10.5" r="7.5"/><path d="m16 16 5 5"/>',
  monitor:
    '<rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8m-4-4v4"/>',
  phone:
    '<rect x="6" y="2" width="12" height="20" rx="3"/><path d="M10 5h4m-3 14h2"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v6m0-10h.01"/>',
  sparkle:
    '<path d="m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5L12 3Z"/>',
  heart: '<path d="M20 5c-3-3-7-1-8 1-1-2-5-4-8-1-6 6 8 15 8 15S26 11 20 5Z"/>',
  link: '<path d="m10 13 4-4m-6 6-2 2a4 4 0 0 1-6-6l5-5a4 4 0 0 1 6 0m2 2 2-2a4 4 0 0 1 6 6l-5 5a4 4 0 0 1-6 0" transform="translate(1 1)"/>',
};
const icon = (name, size = 20) =>
  `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${icons[name] || icons.info}</svg>`;
const e = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const fa = (value) =>
  new Intl.NumberFormat("fa-IR", { maximumFractionDigits: 2 }).format(
    Number(value) || 0,
  );
const date = (value) => {
  try {
    return new Intl.DateTimeFormat("fa-IR", {
      year: "numeric",
      month: "short",
      day: "numeric",
    }).format(new Date(value));
  } catch {
    return "—";
  }
};
const fullDate = () =>
  new Intl.DateTimeFormat("fa-IR", {
    weekday: "long",
    month: "long",
    day: "numeric",
  }).format(new Date());
const cleanNumber = (value) =>
  String(value)
    .replace(/[۰-۹]/g, (n) => "۰۱۲۳۴۵۶۷۸۹".indexOf(n))
    .replace(/[٠-٩]/g, (n) => "٠١٢٣٤٥٦٧٨٩".indexOf(n))
    .replace(/[,٬\s]/g, "")
    .replace("٫", ".");
const tg = window.Telegram?.WebApp;
const state = {
  meta: null,
  data: null,
  page: "home",
  category: "regular",
  renewal: null,
  admin: null,
  adminTab: "plans",
  adminCategory: "regular",
  os: "android",
  historyFilter: "all",
  search: "",
  checkout: null,
  pendingPlan: null,
  error: null,
};
const statusNames = {
  awaiting_receipt: "منتظر رسید",
  review: "در انتظار تأیید",
  provisioning: "در حال فعال‌سازی",
  needs_review: "نیازمند بررسی",
  approved: "تأیید شده",
  rejected: "رد شده",
  cancelled: "لغو شده",
};
const statusTone = {
  awaiting_receipt: "amber",
  review: "amber",
  provisioning: "amber",
  needs_review: "red",
  approved: "green",
  rejected: "red",
  cancelled: "gray",
};
const badge = (status) =>
  `<span class="badge ${statusTone[status] || "gray"}"><i></i>${e(statusNames[status] || status)}</span>`;
const catName = (cat) => (cat === "gaming" ? "گیمینگ" : "عادی");
const catIcon = (cat) => (cat === "gaming" ? "game" : "globe");
const plans = (category = state.category, admin = false) =>
  Object.entries(
    (admin ? state.admin?.catalog : state.data?.catalog)?.plans || {},
  ).filter(([, p]) => p.category === category);
let lastFocus = null;
let receiptBlob = null;

async function api(path, { method = "GET", body } = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 85000);
  try {
    const headers = {};
    if (tg?.initData) headers.Authorization = `tma ${tg.initData}`;
    if (body !== undefined) headers["Content-Type"] = "application/json";
    const response = await fetch(`/api${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: controller.signal,
      cache: "no-store",
    });
    if (
      response.headers.get("content-type")?.startsWith("image/") &&
      response.ok
    )
      return await response.blob();
    const data = await response.json();
    if (!response.ok) {
      const error = new Error(
        data.message || "اطلاعات ارسالی معتبر نیست؛ دوباره بررسی کن.",
      );
      error.code =
        data.code ||
        (response.status === 401 ? "unauthorized" : "request_failed");
      throw error;
    }
    return data;
  } catch (error) {
    if (error.name === "AbortError")
      throw new Error(
        "پاسخ دیر رسید. دوباره پرداخت نکن؛ وضعیت درخواست را از سفارش‌ها یا کانفیگ‌های من بررسی کن.",
      );
    if (error instanceof TypeError)
      throw new Error(
        "ارتباط با سرور برقرار نشد. اینترنتت را بررسی کن و دوباره بزن.",
      );
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

function toast(message, error = false) {
  const item = document.createElement("div");
  item.className = `toast${error ? " error" : ""}`;
  item.innerHTML =
    icon(error ? "info" : "checkCircle") + `<span>${e(message)}</span>`;
  document.getElementById("toasts").replaceChildren(item);
  setTimeout(() => item.remove(), 5000);
}

function handleError(error) {
  if (
    ["unauthorized", "membership_required", "membership_unavailable"].includes(
      error.code,
    )
  ) {
    closeModal();
    state.error = error;
    state.data = null;
    renderGate();
  } else toast(error.message || "مشکلی پیش اومد. دوباره امتحان کن.", true);
}

async function busy(element, job) {
  if (element?.disabled) return;
  const previous = element?.innerHTML;
  if (element) {
    element.disabled = true;
    element.setAttribute("aria-busy", "true");
    element.innerHTML =
      '<span class="loader" aria-hidden="true"></span><span>یه لحظه…</span>';
  }
  try {
    return await job();
  } finally {
    if (element) {
      element.disabled = false;
      element.removeAttribute("aria-busy");
      element.innerHTML = previous;
    }
  }
}

function validWebURL(value) {
  try {
    const url = new URL(value);
    return url.protocol === "https:" ? url.href : "#";
  } catch {
    return "#";
  }
}
function chatURL(username) {
  return /^[a-zA-Z0-9_]{3,64}$/.test(username || "")
    ? `https://t.me/${username}`
    : null;
}
function openLink(value) {
  const url = validWebURL(value);
  if (url === "#") return toast("این لینک هنوز تنظیم نشده است.", true);
  if (url.startsWith("https://t.me/") && tg?.initData) tg.openTelegramLink(url);
  else window.open(url, "_blank", "noopener,noreferrer");
}
async function copy(value, message = "کپی شد؛ آمادهٔ استفاده است!") {
  try {
    await navigator.clipboard.writeText(value);
  } catch {
    const input = document.createElement("textarea");
    input.value = value;
    (document.getElementById("modal").open
      ? document.getElementById("modal")
      : document.body
    ).append(input);
    input.select();
    const ok = document.execCommand("copy");
    input.remove();
    if (!ok) return toast("لطفاً متن لینک را لمس و دستی کپی کن.", true);
  }
  toast(message);
}

function setTheme(theme) {
  document.documentElement.dataset.theme = theme;
  try {
    localStorage.setItem("pinginoo_theme", theme);
  } catch {
    /* Privacy mode */
  }
  document.querySelector("meta[name=theme-color]").content =
    theme === "dark" ? "#191722" : "#f7f8fb";
  if (tg?.initData) {
    tg.setHeaderColor(theme === "dark" ? "#24212f" : "#ffffff");
    tg.setBackgroundColor(theme === "dark" ? "#191722" : "#f7f8fb");
  }
}
try {
  setTheme(localStorage.getItem("pinginoo_theme") || "light");
} catch {
  setTheme("light");
}

function navButton(page, label, glyph, { category, count } = {}) {
  const active =
    state.page === page && (!category || state.category === category);
  return `<button class="nav-item${active ? " active" : ""}" data-action="navigate" data-page="${page}" ${category ? `data-category="${category}"` : ""} ${active ? 'aria-current="page"' : ""}>${icon(glyph)}<span>${label}</span>${count ? `<span class="nav-number">${fa(count)}</span>` : ""}</button>`;
}
function mobileButton(page, label, glyph) {
  return `<button data-action="navigate" data-page="${page}" class="${state.page === page ? "active" : ""}" ${state.page === page ? 'aria-current="page"' : ""}>${icon(glyph)}<span>${label}</span></button>`;
}
function shell() {
  const data = state.data;
  if (!data) return renderGate();
  const activeCount = data.configs.filter((c) => c.active).length;
  const pending = data.orders.filter((o) =>
    ["review", "awaiting_receipt", "needs_review"].includes(o.status),
  ).length;
  document.getElementById("app").innerHTML = `
    <aside class="sidebar" aria-label="منوی اصلی">
      <a href="#home" class="brand" data-action="navigate" data-page="home" aria-label="پینگینو، صفحه اصلی"><img src="/static/assets/logo.svg" alt="" width="46" height="46"><div><div class="brand-name">پینگینو</div><div class="brand-en">PINGINOO</div></div></a>
      <div class="nav-label">فضای پینگینویی تو</div>
      <nav class="side-nav">
        ${navButton("home", "پیشخوان", "home")}
        ${navButton("shop", "خرید کانفیگ عادی", "globe", { category: "regular" })}
        ${navButton("shop", "کانفیگ گیمینگ", "game", { category: "gaming" })}
        ${navButton("configs", "کانفیگ‌های من", "box", { count: activeCount })}
        ${navButton("history", "سفارش‌های من", "receipt", { count: pending })}
        <button class="nav-item" data-action="trial">${icon("gift")}<span>تست رایگان یک‌روزه</span></button>
      </nav>
      <div class="nav-divider"></div><div class="nav-label">ما کنارتیم</div>
      <nav class="side-nav">${navButton("help", "راهنمای اتصال", "book")}${navButton("support", "پشتیبانی", "headset")}${data.is_admin ? navButton("admin", "پنل مدیریت", "settings") : ""}</nav>
      <div class="side-spacer"></div>
      <div class="community-card"><div class="community-icon">${icon("telegram", 21)}</div><h4>عضوی از خانوادهٔ پینگینو</h4><p>خبرها و آموزش‌ها رو از دست نده.</p><a href="${e(validWebURL(state.meta.channel_url))}" target="_blank" rel="noopener noreferrer">کانال پینگینو ${icon("upLeft", 14)}</a></div>
      <div class="sidebar-profile"><div class="avatar">پ</div><div><strong>${e(data.user.first_name)}</strong><small>عضویت کانال تأیید شده</small></div><span class="profile-check" title="عضویت تأیید شده">${icon("shield", 19)}</span></div>
    </aside>
    <div class="workspace">
      <header class="topbar"><div><div class="greeting">سلام، خوش اومدی <span>👋</span></div><p class="greeting-sub">یه روز خوب، با یه اتصال بهتر.</p></div><div class="topbar-tools"><span class="top-date">${e(fullDate())}</span>${state.meta.demo ? '<span class="demo-tag">نسخهٔ نمایشی</span>' : ""}<button class="icon-button refresh-button" data-action="refresh" aria-label="به‌روزرسانی اطلاعات" title="به‌روزرسانی">${icon("refresh", 18)}</button><button class="icon-button theme-button" data-action="theme" aria-label="تغییر حالت روشن و تاریک" title="تغییر رنگ محیط">${icon(document.documentElement.dataset.theme === "dark" ? "sun" : "moon", 18)}</button><button class="icon-button" data-action="notifications" aria-label="اعلان‌ها" title="اعلان‌ها">${icon("bell", 18)}${pending ? '<i class="notification-dot"></i>' : ""}</button></div></header>
      <main class="main" id="main" tabindex="-1"><div id="page-content" class="page-appear">${pageContent()}</div></main>
      <footer class="footer"><span>پینگینو؛ یه دوست برای وصل موندن ${icon("heart")}</span><span>${state.meta.demo ? "پیش‌نمایش تعاملی · بدون پرداخت و کانفیگ واقعی" : "تمام قیمت‌ها به تومان است"} ${icon("shield")}</span></footer>
    </div>
    <nav class="mobile-nav" aria-label="منوی موبایل">${mobileButton("home", "پیشخوان", "home")}${mobileButton("shop", "خرید کانفیگ", "globe")}${mobileButton("configs", "کانفیگ‌ها", "box")}${mobileButton("history", "سفارش‌ها", "receipt")}${data.is_admin ? mobileButton("admin", "مدیریت", "settings") : mobileButton("support", "پشتیبانی", "headset")}</nav>`;
}
function heading(title, subtitle, extra = "") {
  return `<div class="page-heading"><div><h1>${title}</h1><p>${subtitle}</p></div>${extra}</div>`;
}
function sectionHead(title, subtitle = "", extra = "") {
  return `<div class="section-heading"><div><h2>${title}</h2>${subtitle ? `<p>${subtitle}</p>` : ""}</div>${extra}</div>`;
}
function categoryTabs(admin = false) {
  const selected = admin ? state.adminCategory : state.category;
  return `<div class="segmented" role="group" aria-label="نوع کانفیگ">${["regular", "gaming"].map((cat) => `<button data-action="category" data-category="${cat}" ${admin ? 'data-admin="true"' : ""} class="${selected === cat ? "active" : ""}" aria-pressed="${selected === cat}">${icon(catIcon(cat))} کانفیگ ${catName(cat)}</button>`).join("")}</div>`;
}
function quickStats() {
  const count = state.data.configs.filter((c) => c.active).length;
  const trial = state.data.catalog.trial;
  return `<div class="quick-stats">
    <button class="quick-stat clickable" data-action="navigate" data-page="configs"><div class="stat-icon tone-purple">${icon("box", 21)}</div><div><h3>کانفیگ‌های فعال</h3><strong>${fa(count)}</strong><small>اتصال در دسترس</small></div>${icon("chevron", 15).replace("<svg ", '<svg class="stat-arrow" ')}</button>
    <button class="quick-stat clickable" data-action="trial"><div class="stat-icon tone-green">${icon("gift", 21)}</div><div><h3>تست یک‌روزهٔ پینگینو</h3><strong>${state.data.user.trial_used ? "دریافت شد" : "رایگان"}</strong><small>${fa(trial.traffic_gb)} گیگ هدیه برای شروع</small></div>${icon("chevron", 15).replace("<svg ", '<svg class="stat-arrow" ')}</button>
    <button class="quick-stat clickable" data-action="navigate" data-page="support"><div class="stat-icon tone-peach">${icon("headset", 21)}</div><div><h3>پشتیبانی پینگینو</h3><strong>کنارتیم</strong><small>هر وقت کمک خواستی</small></div>${icon("chevron", 15).replace("<svg ", '<svg class="stat-arrow" ')}</button>
  </div>`;
}
function planCards() {
  const list = plans();
  if (!list.length)
    return empty(
      "globe",
      "کمی بعد سر بزن!",
      "در حال حاضر پلن فعالی در این بخش نداریم. پلن‌های بخش دیگر یا تست رایگان را ببین.",
      "trial",
      "دریافت تست رایگان",
    );
  return `<div class="plan-grid">${list
    .map(([key, p], i) => {
      const tagline =
        p.category === "gaming"
          ? ["برای شروع بازی", "برای گیمرهای همیشگی", "برای بازی، بی‌وقفه"][
              i % 3
            ]
          : ["سبک و جمع‌وجور", "همراه هر روز تو", "برای کارهای بزرگ‌تر"][i % 3];
      return `<article class="plan-card${p.featured ? " featured" : ""}">
      <div class="plan-top"><div class="plan-icon">${icon(p.category === "gaming" ? "game" : ["globe", "zap", "sparkle"][i % 3], 21)}</div>${p.featured ? `<span class="popular-tag">${icon("sparkle")} پیشنهاد پینگینو</span>` : `<span class="plan-kicker">${i === 0 ? "یه شروع خوب" : "فضای بیشتر، خیال راحت‌تر"}</span>`}</div>
      <h3>${e(p.name)}</h3><p class="plan-subtitle">${tagline}</p>
      <div class="plan-amount"><strong>${fa(p.traffic_gb)}</strong><span>گیگابایت</span></div><div class="plan-duration">${icon("calendar")} اعتبار ${fa(p.days)} روزه</div>
      <ul class="plan-features"><li>${icon("checkCircle")} لینک اشتراک اختصاصی</li><li>${icon("checkCircle")} موبایل و دسکتاپ</li><li>${icon("checkCircle")} راهنمای اتصال و پشتیبانی</li></ul>
      <div class="plan-price"><strong>${fa(p.price)}</strong><span>تومان</span><small>/ ${fa(p.days)} روز</small></div>
      <button class="btn btn-full ${p.featured ? "btn-primary" : "btn-outline"}" data-action="select-plan" data-id="${e(key)}">${state.renewal ? "انتخاب برای تمدید" : "انتخاب این پلن"} ${icon("arrow")}</button>
    </article>`;
    })
    .join("")}</div>`;
}
function trialStrip() {
  const trial = state.data.catalog.trial;
  return `<section class="trial-strip"><div class="trial-strip-icon">${icon("gift", 27)}</div><div><h3>قبل از خرید، دوستش داشته باش.</h3><p>یک روز مهمون ما باش؛ ${fa(trial.traffic_gb)} گیگ اینترنت برای امتحان کردن پینگینو.</p></div><button class="btn" data-action="trial">تست رایگان یک‌روزه ${icon("arrow")}</button></section>`;
}
function shopSection(home = false) {
  return `${sectionHead(home ? "پلن تو کدومه؟" : `پلن‌های ${catName(state.category)}`, home ? "یه انتخاب ساده، برای هر جور استفاده." : "قیمت شفاف، حجم مشخص؛ متناسب با نیازت انتخاب کن.", categoryTabs())}
    ${planCards()}${state.category === "gaming" ? `<p class="category-note">${icon("info")} پلن‌های گیمینگ جدا هستند؛ پینگ و کیفیت نهایی به اینترنت و مسیر سرور بستگی دارد.</p>` : ""}`;
}
function homePage() {
  return `${heading("خونهٔ پینگینویی تو", "همه‌چیز برای یه اتصال خوب، همین‌جاست.", `<div class="verified">${icon("shield", 15)}<span class="label">عضویت کانال تأیید شده</span><i class="dot"></i></div>`)}
    <section class="hero"><div class="hero-copy"><div class="hero-eyebrow"><i></i> YOUR WORLD. CONNECTED.</div><h2>دنیای تو، <span>بدون مرز.</span></h2><p>از گشت‌وگذارهای روزمره تا هیجان بازی؛<br>اتصالی که با سبک زندگی تو همراه می‌شه.</p><div class="hero-actions"><button class="btn btn-mint" data-action="navigate" data-page="shop" data-category="regular">کانفیگ خودتو پیدا کن ${icon("arrow")}</button><button class="text-link hero-link" data-action="trial">${icon("gift", 16)} اول رایگان امتحان کن</button></div></div><div class="hero-art"><img src="/static/assets/pingino-hero.webp" alt="پنگوئن پینگینو با هدفون بنفش و شال سبز" width="370" height="370" fetchpriority="high"></div><span class="hero-cross">${icon("sparkle", 21)}</span><div class="hero-float">${icon("shield", 24)}<div>یه همراه برای اتصال<small>با پینگینو، به سبک خودت!</small></div></div></section>
    ${quickStats()}${shopSection(true)}${trialStrip()}
    <div class="bottom-panels"><section class="mini-panel"><div class="stat-icon tone-purple">${icon("book")}</div><div><h3>اولین باره اینجایی؟</h3><p>فقط چند قدم تا دنیای پینگینو.</p></div><button class="text-link" data-action="navigate" data-page="help">راهنمای اتصال ${icon("arrow")}</button></section><section class="mini-panel"><div class="stat-icon tone-peach">${icon("headset")}</div><div><h3>یه سوال کوچیک داری؟</h3><p>با هم راهش رو پیدا می‌کنیم.</p></div><button class="text-link" data-action="navigate" data-page="support">حرف بزنیم ${icon("arrow")}</button></section></div>`;
}
function shopPage() {
  return `${heading(state.category === "gaming" ? "بازی کن، به سبک پینگینو." : "اتصالی که به تو میاد.", "پلن‌های عادی و گیمینگ، جدا و متناسب با نیازت.")}
    ${state.renewal ? `<div class="renewal-banner">${icon("refresh")}<div>تمدید ${e(state.renewal.plan_name)}<small>همان لینک قبلی حفظ می‌شود؛ فقط پلن‌های هم‌نوع قابل انتخاب‌اند.</small></div><button class="icon-button" data-action="cancel-renewal" aria-label="انصراف از تمدید">${icon("close", 16)}</button></div>` : ""}
    ${shopSection()}${trialStrip()}<section class="panel"><h2>از انتخاب تا اتصال، سه قدم کوتاه.</h2><div class="flow-steps"><div class="flow-step"><span class="step-num">۱</span><div><h3>پلنت رو انتخاب کن</h3><p>حجم و مدت مناسب خودت را انتخاب و سفارش را ثبت کن.</p></div></div><div class="flow-step"><span class="step-num">۲</span><div><h3>رسیدت رو بفرست</h3><p>مبلغ فاکتور را واریز و عکس رسید را در ربات ارسال کن.</p></div></div><div class="flow-step"><span class="step-num">۳</span><div><h3>به دنیات وصل شو</h3><p>بعد از تأیید ادمین، لینک آمادهٔ ورود به برنامهٔ اتصال است.</p></div></div></div></section>`;
}
function empty(glyph, title, description, action, label, page = "") {
  return `<div class="empty-state"><div class="stat-icon tone-purple">${icon(glyph, 29)}</div><h3>${title}</h3><p>${description}</p>${action ? `<button class="btn btn-primary" data-action="${action}" ${page ? `data-page="${page}"` : ""}>${label} ${icon("arrow")}</button>` : ""}</div>`;
}
function configPage() {
  return `${heading("کانفیگ‌های من", "اتصال‌های تو؛ همیشه همین‌جا در دسترس.", `<button class="btn btn-primary" data-action="navigate" data-page="shop">${icon("plus")} کانفیگ جدید</button>`)}
    ${state.meta.demo ? '<div class="info-banner demo-notice">' + icon("info") + "<p>اطلاعات و لینک‌ها نمایشی‌اند. کانفیگ این پیش‌نمایش برای اتصال واقعی قابل استفاده نیست.</p></div>" : ""}
    ${
      state.data.configs.length
        ? `<div class="configs-grid">${state.data.configs
            .map((cfg) => {
              const days = Math.max(
                0,
                Math.ceil((new Date(cfg.expires_at) - Date.now()) / 86400000),
              );
              const percent = Math.max(
                0,
                Math.min(100, (days / (cfg.days || 30)) * 100),
              );
              return `<article class="config-card"><div class="config-card-head"><div class="stat-icon ${cfg.is_trial ? "tone-green" : "tone-purple"}">${icon(cfg.is_trial ? "gift" : catIcon(cfg.category))}</div><div><h3>${e(cfg.plan_name)}</h3><p>کانفیگ ${catName(cfg.category)} ${cfg.is_trial ? "· تست رایگان" : ""}</p></div><span class="badge ${cfg.active ? "green" : "gray"}"><i></i>${cfg.active ? "فعال" : "منقضی"}</span></div><div class="config-metrics"><div><label>حجم پلن</label><strong>${fa(cfg.traffic_gb)}<span>گیگابایت</span></strong></div><div><label>زمان باقی‌مانده</label><strong>${fa(days)}<span>روز</span></strong></div></div><div class="config-expiry"><span>اعتبار اشتراک</span><span>تا ${date(cfg.expires_at)}</span></div><div class="progress-track" role="img" aria-label="${fa(days)} روز از اعتبار باقی مانده"><i style="width:${percent}%"></i></div><div class="config-card-actions"><button class="btn btn-primary" data-action="config" data-id="${e(cfg.id)}">${icon("link")} مشاهده و کپی لینک</button>${cfg.renewable ? `<button class="btn btn-outline" data-action="renew" data-id="${e(cfg.id)}">${icon("refresh")} تمدید</button>` : ""}</div></article>`;
            })
            .join(
              "",
            )}</div><p class="category-note" style="margin-top:18px">${icon("info")} حجم نمایش‌داده‌شده حجم پلن است، نه مصرف لحظه‌ای. نوار، زمان اعتبار را نشان می‌دهد.</p>`
        : empty(
            "box",
            "جای اولین اتصالت خالیه!",
            "با یک تست رایگان شروع کن و بعد پلن مناسب خودت را انتخاب کن.",
            "trial",
            "دریافت تست یک‌روزه",
          )
    }`;
}
function orderRows() {
  const query = state.search.trim().toLowerCase();
  const list = state.data.orders.filter(
    (p) =>
      (state.historyFilter === "all" || p.status === state.historyFilter) &&
      (!query || `${p.id} ${p.plan_name}`.toLowerCase().includes(query)),
  );
  if (!list.length)
    return empty(
      "receipt",
      "سفارشی پیدا نشد.",
      state.data.orders.length
        ? "فیلتر یا عبارت جستجو را تغییر بده."
        : "اولین سفارشت که ثبت شود، جزئیات و وضعیتش را اینجا می‌بینی.",
    );
  return `<div class="table-wrap" tabindex="0" role="region" aria-label="جدول اطلاعات"><table><thead><tr><th>سفارش</th><th>مبلغ</th><th>تاریخ ثبت</th><th>وضعیت</th><th><span class="sr-only">جزئیات</span></th></tr></thead><tbody>${list.map((p) => `<tr><td><div class="cell-plan"><div class="stat-icon tone-purple">${icon(catIcon(p.category))}</div><div><strong>${e(p.plan_name)}</strong><small class="ltr">${e(p.id)}</small></div></div></td><td><strong>${fa(p.price)}</strong> تومان</td><td>${date(p.created_at)}</td><td>${badge(p.status)}</td><td><button class="btn btn-light btn-small" data-action="order" data-id="${e(p.id)}">جزئیات ${icon("chevron", 13)}</button></td></tr>`).join("")}</tbody></table></div>`;
}
function historyPage() {
  return `${heading("سفارش‌های من", "از اولین انتخاب تا لحظهٔ اتصال، همه‌چیز قابل پیگیریه.")}<div class="table-toolbar"><label class="search-field">${icon("search")}<input id="order-search" placeholder="جستجوی نام یا شناسهٔ سفارش…" aria-label="جستجوی سفارش" value="${e(state.search)}"></label><select id="order-filter" class="select-field" aria-label="فیلتر وضعیت سفارش"><option value="all">همهٔ سفارش‌ها</option>${Object.entries(
    statusNames,
  )
    .map(
      ([key, name]) =>
        `<option value="${key}" ${state.historyFilter === key ? "selected" : ""}>${name}</option>`,
    )
    .join(
      "",
    )}</select></div><div id="history-results">${orderRows()}</div><div class="support-note">${icon("info", 16)} بعد از ارسال عکس رسید در ربات، سفارش وارد صف بررسی می‌شود. لازم نیست دوباره پرداخت کنی؛ وضعیت از همین بخش به‌روز می‌شود.</div>`;
}
const faq = [
  [
    "تست رایگان چطور کار می‌کنه؟",
    "هر حساب تلگرام فقط یک‌بار می‌تواند تست بگیرد. اعتبار تست از زمان فعال‌سازی، ۲۴ ساعت است. حجم و فعال بودن تست توسط ادمین تعیین می‌شود.",
  ],
  [
    "چطور کانفیگ رو دریافت کنم؟",
    "بعد از ثبت سفارش، مبلغ دقیق را کارت‌به‌کارت و عکس رسید را در ربات ارسال کن. پس از بررسی و تأیید ادمین، لینک به ربات ارسال می‌شود و در «کانفیگ‌های من» هم موجود خواهد بود.",
  ],
  [
    "تفاوت پلن عادی و گیمینگ چیه؟",
    "پلن‌های عادی و گیمینگ کاتالوگ و تنظیمات جدا دارند. کیفیت و پینگ به اینترنت و مسیر سرور وابسته است. برای اطمینان از مناسب بودن مسیر بازی، قبل از خرید از پشتیبانی راهنمایی بگیر.",
  ],
  [
    "با تمدید، لینک کانفیگ عوض می‌شه؟",
    "از دکمهٔ تمدید همان کانفیگ استفاده کن. بعد از تأیید پرداخت، همان اشتراک در پنل تمدید می‌شود و لینک قبلی باقی می‌ماند. پلن تمدید باید هم‌نوع کانفیگ فعلی باشد.",
  ],
  [
    "باید عضو کانال بمونم؟",
    "بله. برای استفاده از امکانات ربات و مینی‌اپ، عضویت کانال بررسی می‌شود. اگر خارج شده‌ای، دوباره عضو شو و دکمهٔ بررسی عضویت را بزن.",
  ],
  [
    "رسید فرستادم ولی هنوز فعال نشده.",
    "تأیید پرداخت توسط ادمین انجام می‌شود. در «سفارش‌های من» وضعیت را بررسی کن. اگر نیاز به پیگیری داشتی، فقط شناسهٔ سفارش را برای پشتیبانی بفرست؛ دوباره پرداخت نکن.",
  ],
];
function faqList(items = faq) {
  return `<div class="faq-list">${items.map(([q, a]) => `<details><summary>${q}</summary><p>${a}</p></details>`).join("")}</div>`;
}
function guideContent() {
  const guide = {
    android: {
      app: "v2rayNG یا Hiddify",
      url: "https://github.com/2dust/v2rayNG/releases",
      kind: "گوشی اندرویدی",
    },
    ios: {
      app: "Streisand یا Hiddify",
      url: "https://apps.apple.com/app/streisand/id6450534064",
      kind: "آیفون یا آیپد",
    },
    desktop: {
      app: "Hiddify",
      url: "https://github.com/hiddify/hiddify-app/releases",
      kind: "کامپیوتر",
    },
  }[state.os];
  return `<ol class="guide-list"><li><span class="step-num">۱</span><div><h3>برنامهٔ اتصال را نصب کن</h3><p>برای ${guide.kind} می‌توانی از ${guide.app} استفاده کنی. نسخهٔ رسمی و به‌روز را نصب کن.</p><a class="text-link" href="${guide.url}" target="_blank" rel="noopener noreferrer">دریافت از منبع رسمی ${icon("upLeft")}</a></div></li><li><span class="step-num">۲</span><div><h3>لینک اشتراکت را کپی کن</h3><p>از بخش «کانفیگ‌های من»، روی مشاهده و کپی لینک بزن. لینک را برای دیگران نفرست.</p><button class="text-link" data-action="navigate" data-page="configs">رفتن به کانفیگ‌های من ${icon("arrow")}</button></div></li><li><span class="step-num">۳</span><div><h3>اضافه کن و وصل شو</h3><p>در برنامه، افزودن اشتراک از کلیپ‌بورد (Import from clipboard) را بزن، اشتراک را به‌روز کن، یک سرور انتخاب کن و اتصال را روشن کن.</p></div></li></ol>`;
}
function helpPage() {
  return `${heading("فقط چند قدم تا اتصال.", "اولین باره؟ با هم راه می‌افتیم.")}<div class="faq-grid"><section class="panel"><div class="help-heading"><img src="/static/assets/logo.svg" alt=""><div><h2>راهنمای شروع سریع</h2><p>با چه دستگاهی می‌خوای وصل بشی؟</p></div></div><div class="os-tabs" role="group" aria-label="دستگاه شما">${[
    ["android", "اندروید", "phone"],
    ["ios", "آیفون", "phone"],
    ["desktop", "دسکتاپ", "monitor"],
  ]
    .map(
      ([id, name, glyph]) =>
        `<button class="btn btn-outline ${state.os === id ? "selected" : ""}" data-action="os" data-os="${id}" aria-pressed="${state.os === id}">${icon(glyph)} ${name}</button>`,
    )
    .join(
      "",
    )}</div><div id="guide-content">${guideContent()}</div></section><section><h2 class="faq-heading">سوال‌های پرتکرار</h2>${faqList()}</section></div>`;
}
function supportPage() {
  const support = chatURL(state.meta.support_username);
  return `${heading("یه سوال کوچیک یا یه مشکل بزرگ؟", "توی پینگینو، قرار نیست تنهایی حلش کنی.")}<section class="support-hero">${icon("headset", 74)}<div><h2>با هم راهش رو پیدا می‌کنیم.</h2><p>برای راهنمایی خرید، مشکل اتصال یا پیگیری سفارش، کنار تو هستیم.</p>${support ? `<a class="btn btn-mint" href="${support}" target="_blank" rel="noopener noreferrer">${icon("telegram")} گفتگو با پشتیبانی ${icon("upLeft")}</a>` : `<button class="btn btn-mint" data-action="channel">${icon("telegram")} اطلاعیه‌های کانال ${icon("upLeft")}</button>`}</div></section>${!support ? '<div class="info-banner"><p>آدرس مستقیم پشتیبانی هنوز توسط مدیر ثبت نشده. فعلاً راهنما و اطلاعیه‌های کانال را ببین.</p></div>' : ""}<div class="faq-grid"><div><h2 class="faq-heading">شاید جواب همین‌جا باشه.</h2>${faqList(faq.slice(1, 4))}</div><section class="panel"><h2>برای پیگیری سریع‌تر</h2><p class="panel-desc">قبل از فرستادن پیام، این موارد را آماده کن:</p><ol class="guide-list"><li><span class="step-num">۱</span><p>شناسهٔ سفارش یا نام کانفیگ را از بخش حساب خودت کپی کن.</p></li><li><span class="step-num">۲</span><p>نوع دستگاه، اپراتور اینترنت و توضیح کوتاهی از مشکل را بفرست.</p></li><li><span class="step-num">۳</span><p>در صورت نیاز، عکس خطا را بدون نمایش لینک خصوصی بفرست.</p></li></ol><div class="support-note">رمز حساب، رمز دوم و اطلاعات کامل کارت بانکی را برای هیچ‌کس ارسال نکن.</div><button class="btn btn-outline btn-full" data-action="navigate" data-page="history">مشاهدهٔ سفارش‌های من ${icon("arrow")}</button></section></div>`;
}
function pageContent() {
  return (
    {
      home: homePage,
      shop: shopPage,
      configs: configPage,
      history: historyPage,
      help: helpPage,
      support: supportPage,
      admin: adminPage,
    }[state.page] || homePage
  )();
}

function adminStats() {
  const stats = state.admin.stats;
  return `<div class="quick-stats admin-stats">${[
    ["users", "tone-purple", "کاربران", stats.users, "نفر"],
    ["box", "tone-green", "کانفیگ فعال", stats.active_configs, "اتصال"],
    ["wallet", "tone-purple", "فروش تأییدشده", stats.revenue, "تومان"],
    ["receipt", "tone-peach", "در انتظار بررسی", stats.pending, "سفارش"],
  ]
    .map(
      ([glyph, tone, label, value, unit]) =>
        `<div class="quick-stat ${glyph === "wallet" ? "stat-revenue" : ""}"><div class="stat-icon ${tone}">${icon(glyph)}</div><div><h3>${label}</h3><strong>${fa(value)}</strong><small>${unit}</small></div></div>`,
    )
    .join("")}</div>`;
}
function adminPage() {
  if (!state.data.is_admin)
    return empty(
      "shield",
      "این بخش خصوصی است.",
      "مدیریت فقط برای ادمین‌های ثبت‌شدهٔ ربات فعال است.",
    );
  if (!state.admin)
    return `<div class="loading-panel"><span class="loader"></span><p>داریم داشبورد مدیریت رو آماده می‌کنیم…</p></div>`;
  return `${heading("پنل مدیریت پینگینو", "کنترل همه‌چیز، دست توئه.", `<span class="badge">${icon("shield", 13)} دسترسی ادمین</span>`)}${adminStats()}<div class="admin-tabs" role="group" aria-label="بخش مدیریت">${[
    ["plans", "پلن‌ها و قیمت‌ها", "globe"],
    ["orders", "سفارش‌ها", "receipt"],
    ["trial", "تست رایگان", "gift"],
    ["users", "کاربران", "users"],
  ]
    .map(
      ([tab, name, glyph]) =>
        `<button data-action="admin-tab" data-tab="${tab}" class="${state.adminTab === tab ? "active" : ""}" aria-pressed="${state.adminTab === tab}">${icon(glyph)} ${name}</button>`,
    )
    .join(
      "",
    )}</div>${({ plans: adminPlans, orders: adminOrders, trial: adminTrial, users: adminUsers }[state.adminTab] || adminPlans)()}`;
}
function adminPlans() {
  const list = plans(state.adminCategory, true);
  return `${sectionHead("پلن‌ها، به انتخاب تو", "قیمت و حجم جدید فقط برای سفارش‌های بعدی اعمال می‌شود.", categoryTabs(true))}<div class="table-wrap" tabindex="0" role="region" aria-label="جدول اطلاعات"><table><thead><tr><th>نام پلن</th><th>حجم</th><th>مدت</th><th>قیمت به تومان</th><th>وضعیت</th><th>ویرایش</th></tr></thead><tbody>${list.map(([id, p]) => `<tr><td><div class="cell-plan"><div class="stat-icon tone-purple">${icon(catIcon(p.category))}</div><div><strong>${e(p.name)}</strong><small>کانفیگ ${catName(p.category)}</small></div></div></td><td>${fa(p.traffic_gb)} گیگ</td><td>${fa(p.days)} روز</td><td><strong>${fa(p.price)}</strong></td><td><span class="badge ${p.enabled ? "green" : "gray"}"><i></i>${p.enabled ? "فعال" : "غیرفعال"}</span></td><td><button class="btn btn-light btn-small" data-action="edit-plan" data-id="${e(id)}" aria-label="ویرایش ${e(p.name)}">${icon("edit", 14)} ویرایش</button></td></tr>`).join("")}</tbody></table></div><div class="support-note">${icon("info", 16)} تغییرات بلافاصله در ربات و مینی‌اپ ذخیره می‌شوند. سفارش‌های ثبت‌شده، قیمت و حجم زمان ثبت خودشان را حفظ می‌کنند. غیرفعال کردن پلن، کانفیگ‌های خریداری‌شده را قطع نمی‌کند.</div>`;
}
function adminOrders() {
  const sorted = [...state.admin.orders].sort(
    (a, b) =>
      (["review", "needs_review", "provisioning"].includes(b.status) ? 1 : 0) -
      (["review", "needs_review", "provisioning"].includes(a.status) ? 1 : 0),
  );
  return `${sectionHead("رسیدها و سفارش‌ها", "ابتدا تصویر رسید را بررسی کن؛ سپس فعال‌سازی را تأیید کن.")}<div class="table-wrap" tabindex="0" role="region" aria-label="جدول اطلاعات"><table><thead><tr><th>سفارش</th><th>کاربر</th><th>مبلغ</th><th>وضعیت</th><th>جزئیات</th></tr></thead><tbody>${sorted.map((p) => `<tr><td><strong>${e(p.plan_name)}</strong><small class="ltr">${e(p.id)}</small></td><td class="ltr">${e(p.user_id)}</td><td>${fa(p.price)} تومان</td><td>${badge(p.status)}</td><td><button class="btn btn-light btn-small" data-action="admin-order" data-id="${e(p.id)}">${icon("receipt", 14)} بررسی سفارش</button></td></tr>`).join("") || '<tr><td colspan="5">سفارشی ثبت نشده است.</td></tr>'}</tbody></table></div>`;
}
function adminTrial() {
  const trial = state.admin.catalog.trial;
  return `<section class="panel trial-settings"><div class="admin-banner"><div class="stat-icon tone-green">${icon("gift")}</div><div><h2>اولین اتصال، مهمان پینگینو.</h2><p>تنظیمات تست رایگان برای کاربران جدید.</p></div></div><form id="trial-settings-form"><div class="form-grid"><div class="form-field"><label for="trial-volume">حجم تست (گیگابایت)</label><input id="trial-volume" name="traffic_gb" inputmode="decimal" value="${e(trial.traffic_gb)}" required><small>از ۰٫۱ تا ۱۰۰۰ گیگابایت</small></div><div class="form-field"><label for="trial-days">مدت اعتبار</label><input id="trial-days" value="۱ روز · ۲۴ ساعت" readonly></div><div class="form-field full"><label for="trial-category">نوع کانفیگ تست</label><select name="category" id="trial-category"><option value="regular" ${trial.category === "regular" ? "selected" : ""}>کانفیگ عادی</option><option value="gaming" ${trial.category === "gaming" ? "selected" : ""}>کانفیگ گیمینگ</option></select></div></div><label class="switch"><input type="checkbox" name="enabled" ${trial.enabled ? "checked" : ""}> تست رایگان فعال باشد</label><p class="modal-note">مدت تست همیشه یک‌روزه است. با تغییر این تنظیمات، حق تست کاربرانی که قبلاً تست گرفته‌اند دوباره فعال نمی‌شود.</p><div class="form-error" role="alert"></div><button class="btn btn-primary" type="submit">ذخیرهٔ تنظیمات ${icon("check")}</button></form></section>`;
}
function adminUsers() {
  return `${sectionHead("خانوادهٔ پینگینو", "۱۰۰ کاربر اخیر و وضعیت دریافت تست.")}<div class="table-wrap" tabindex="0" role="region" aria-label="جدول اطلاعات"><table><thead><tr><th>کاربر</th><th>شناسهٔ تلگرام</th><th>تاریخ عضویت در ربات</th><th>تست رایگان</th><th>عملیات</th></tr></thead><tbody>${state.admin.users.map((u) => `<tr><td><strong>${e(u.first_name)}</strong><small>${u.username ? `@${e(u.username)}` : "بدون نام کاربری"}</small></td><td class="ltr">${e(u.id)}</td><td>${date(u.created_at)}</td><td><span class="badge ${u.trial_used ? "green" : "gray"}">${u.trial_used ? "دریافت شده" : ["needs_review", "provisioning"].includes(u.trial_status) ? "نیازمند بررسی" : "دریافت نشده"}</span></td><td>${["needs_review", "provisioning"].includes(u.trial_status) ? `<button class="btn btn-light btn-small" data-action="recover-trial" data-id="${e(u.id)}">بازیابی تست</button>` : "—"}</td></tr>`).join("")}</tbody></table></div><div class="support-note">ارسال همگانی همراه با پیش‌نمایش و تأیید نهایی، از پنل مدیریت داخل ربات در دسترس است.</div>`;
}

function modal(title, subtitle, content) {
  const dialog = document.getElementById("modal");
  if (!dialog.open) lastFocus = document.activeElement;
  dialog.innerHTML = `<div class="modal-head"><div><h2 id="modal-title">${title}</h2>${subtitle ? `<p>${subtitle}</p>` : ""}</div><button class="icon-button" data-action="close-modal" aria-label="بستن پنجره">${icon("close", 16)}</button></div><div class="modal-body">${content}</div>`;
  if (!dialog.open) dialog.showModal();
}
function closeModal() {
  const dialog = document.getElementById("modal");
  dialog.close();
  if (receiptBlob) {
    URL.revokeObjectURL(receiptBlob);
    receiptBlob = null;
  }
  if (lastFocus?.isConnected) lastFocus.focus();
}
function summary(order) {
  return `<div class="order-summary"><div class="summary-row"><span>پلن انتخابی</span><strong>${e(order.plan_name || order.name)}</strong></div><div class="summary-row"><span>نوع کانفیگ</span><strong>${catName(order.category)}</strong></div><div class="summary-row"><span>حجم و اعتبار</span><strong>${fa(order.traffic_gb)} گیگ · ${fa(order.days)} روز</strong></div><div class="summary-row total"><span>مبلغ نهایی</span><strong>${fa(order.price)} <small>تومان</small></strong></div></div>`;
}
function showPlan(id) {
  const plan = state.data.catalog.plans[id];
  if (!plan)
    return toast("این پلن دیگر در دسترس نیست؛ اطلاعات را به‌روز کن.", true);
  state.pendingPlan = id;
  modal(
    state.renewal ? "یه نفس تازه برای اتصالت." : "انتخاب خوبی کردی!",
    "جزئیات را بررسی کن و سفارشت را ثبت کن.",
    `${summary(plan)}${state.renewal ? `<p class="modal-note">${icon("refresh", 15)} تمدید ${e(state.renewal.plan_name)} با حفظ لینک قبلی.</p>` : ""}${state.meta.demo ? '<div class="info-banner demo-notice"><p>این سفارش آزمایشی است؛ هیچ مبلغی واریز نکن. داده‌ها از ربات واقعی جدا هستند.</p></div>' : '<p class="modal-note">پرداخت کارت‌به‌کارت است. بعد از واریز، عکس رسید را داخل ربات بفرست. فعال‌سازی پس از تأیید ادمین انجام می‌شود.</p>'}<div class="modal-actions"><button class="btn btn-primary" data-action="create-order">ثبت سفارش و ادامه ${icon("arrow")}</button><button class="btn btn-outline" data-action="close-modal">برگشت</button></div>`,
  );
}
function paymentModal(data) {
  state.checkout = data;
  const order = data.order;
  const awaiting = order.status === "awaiting_receipt";
  modal(
    awaiting ? "یه قدم تا اتصال." : "جزئیات سفارشت",
    `شناسه: <span class="ltr">${e(order.id)}</span>`,
    `${summary(order)}${!awaiting ? `<div class="summary-row"><span>وضعیت سفارش</span>${badge(order.status)}</div>` : ""}
    ${awaiting ? `<div class="bank-card"><div class="bank-card-top"><span>پرداخت کارت‌به‌کارت</span>${state.meta.demo ? "<span>نمایشی — پرداخت نکنید</span>" : icon("wallet", 20)}</div><div class="card-number ltr">${e(data.payment.card_number || "تنظیم نشده")}</div><div class="card-holder"><span>${e(data.payment.card_name)}</span><button class="text-link" data-action="copy-card">${icon("copy", 13)} کپی</button></div></div><p class="modal-note">${state.meta.demo ? "در حالت نمایشی، دکمهٔ زیر فقط یک رسید آزمایشی در صف مدیریت ثبت می‌کند. هیچ پولی جابه‌جا نمی‌شود." : "مبلغ دقیق فاکتور را واریز کن؛ بعد برای ارسال عکس رسید به ربات برگرد. این سفارش تا زمان تأیید ادمین فعال نمی‌شود."}</p><div class="modal-actions"><button class="btn btn-primary" data-action="send-receipt" ${!state.meta.demo && !data.receipt_url ? "disabled" : ""}>${icon("receipt")} ${state.meta.demo ? "ثبت رسید آزمایشی" : "ارسال رسید در ربات"}</button><button class="btn btn-ghost" data-action="cancel-order" data-id="${e(order.id)}">لغو سفارش</button></div>${!state.meta.demo && !data.receipt_url ? '<div class="form-error">نام کاربری ربات هنوز تنظیم نشده؛ پنجره را ببند و از منوی سفارش‌های داخل ربات رسید را بفرست.</div>' : ""}` : `<p class="modal-note">${order.status === "approved" ? "کانفیگ فعال شده و لینک آن در «کانفیگ‌های من» در دسترس است." : order.status === "rejected" ? "این رسید تأیید نشده. برای بررسی دلیل و پیگیری، با پشتیبانی تماس بگیر." : order.status === "cancelled" ? "این سفارش لغو شده است. هر زمان خواستی، می‌توانی پلن جدیدی انتخاب کنی." : "درخواستت در صف بررسی است؛ نیازی به پرداخت مجدد نیست."}</p><button class="btn btn-primary btn-full" data-action="modal-navigate" data-page="${order.status === "approved" ? "configs" : "history"}">${order.status === "approved" ? "دریافت کانفیگ" : "بازگشت به سفارش‌ها"} ${icon("arrow")}</button>`}`,
  );
}
function trialModal() {
  const user = state.data.user;
  const trial = state.data.catalog.trial;
  if (user.trial_used) {
    modal(
      "اولین هدیه‌ات رو گرفتی.",
      "تست هر حساب فقط یک‌بار قابل دریافت است.",
      `<div class="modal-lead-icon">${icon("checkCircle", 31)}</div><p class="modal-note">لینک تست قبلی در «کانفیگ‌های من» باقی می‌ماند. اگر تجربه‌اش را دوست داشتی، پلن مناسب خودت را انتخاب کن.</p><button class="btn btn-primary btn-full" data-action="modal-navigate" data-page="configs">مشاهدهٔ کانفیگ‌های من ${icon("arrow")}</button>`,
    );
    return;
  }
  const blocked =
    !trial.enabled ||
    ["provisioning", "needs_review"].includes(user.trial_status);
  modal(
    "اول امتحان کن، بعد انتخاب کن.",
    "یه روز مهمون پینگینو باش.",
    `<div class="modal-lead-icon">${icon("gift", 31)}</div><div class="modal-lead"><h3>${fa(trial.traffic_gb)} گیگ، کاملاً رایگان.</h3><p>اعتبار ۲۴ ساعت از زمان فعال‌سازی<br>بدون پرداخت، فقط یک‌بار برای هر حساب تلگرام.</p></div>${state.meta.demo ? '<div class="info-banner demo-notice"><p>تست پیش‌نمایش فقط در داده‌های نمایشی ساخته می‌شود و اتصال واقعی ندارد.</p></div>' : ""}${blocked ? `<div class="review-warning">${!trial.enabled ? "تست رایگان موقتاً غیرفعال است. کمی بعد سر بزن." : "درخواست قبلی در حال پردازش یا بررسی پنل است. برای جلوگیری از ساخت تکراری، درخواست تازه ثبت نمی‌شود."}</div><button class="btn btn-outline btn-full" data-action="modal-navigate" data-page="support">پیگیری از پشتیبانی</button>` : '<button class="btn btn-primary btn-full" data-action="claim-trial">' + icon("gift") + " دریافت تست یک‌روزه</button>"}`,
  );
}
function configModal(id) {
  const cfg = state.data.configs.find((c) => c.id === id);
  if (!cfg) return toast("کانفیگ پیدا نشد.", true);
  modal(
    e(cfg.plan_name),
    "لینک خصوصی اتصال تو، همیشه در دسترس.",
    `<div class="order-summary"><div class="summary-row"><span>وضعیت</span><span class="badge ${cfg.active ? "green" : "gray"}">${cfg.active ? "فعال" : "منقضی"}</span></div><div class="summary-row"><span>حجم پلن</span><strong>${fa(cfg.traffic_gb)} گیگابایت</strong></div><div class="summary-row"><span>تاریخ انقضا</span><strong>${date(cfg.expires_at)}</strong></div></div>${cfg.config_link ? `<div class="copy-field">${e(cfg.config_link)}</div>` : '<div class="review-warning">لینک هنوز در دسترس نیست؛ با پشتیبانی تماس بگیر.</div>'}<p class="modal-note">${state.meta.demo ? "این لینک نمایشی است و برای اتصال واقعی کار نمی‌کند." : "لینک را کپی کن و از گزینهٔ Import from clipboard در برنامهٔ اتصال استفاده کن. اشتراک را به‌روز کن و وصل شو."}</p><div class="modal-actions"><button class="btn btn-primary" data-action="copy-config" data-id="${e(id)}" ${!cfg.config_link ? "disabled" : ""}>${icon("copy")} کپی لینک</button><button class="btn btn-outline" data-action="modal-navigate" data-page="help">${icon("book")} راهنمای اتصال</button></div>`,
  );
}
function editPlanModal(id) {
  const plan = state.admin.catalog.plans[id];
  modal(
    "همون پلن، با شرایط جدید.",
    e(plan.name),
    `<form id="edit-plan-form" data-id="${e(id)}"><div class="form-grid"><div class="form-field full"><label for="plan-name">نام پلن</label><input name="name" id="plan-name" value="${e(plan.name)}" required minlength="2" maxlength="40"></div><div class="form-field full"><label for="plan-price">قیمت (تومان)</label><input name="price" id="plan-price" inputmode="numeric" value="${e(plan.price)}" required><small>بین ۱٬۰۰۰ تا ۱٬۰۰۰٬۰۰۰٬۰۰۰ تومان</small></div><div class="form-field"><label for="plan-volume">حجم (گیگابایت)</label><input name="traffic_gb" id="plan-volume" inputmode="decimal" value="${e(plan.traffic_gb)}" required><small>حداقل ۰٫۱ گیگابایت</small></div><div class="form-field"><label for="plan-days">مدت (روز)</label><input name="days" id="plan-days" inputmode="numeric" value="${e(plan.days)}" required><small>بین ۱ تا ۳۶۵۰ روز</small></div></div><label class="switch" style="margin-top:20px"><input type="checkbox" name="enabled" ${plan.enabled ? "checked" : ""}> پلن برای خرید فعال باشد</label><p class="modal-note">سفارش‌های قبلی تغییر نمی‌کنند. قیمت و حجم تازه برای خریدهای بعدی ذخیره می‌شود.</p><div class="form-error" role="alert"></div><div class="modal-actions"><button type="submit" class="btn btn-primary">ذخیرهٔ تغییرات ${icon("check")}</button><button type="button" class="btn btn-outline" data-action="close-modal">انصراف</button></div></form>`,
  );
}
async function adminOrderModal(id) {
  const order = state.admin.orders.find((o) => o.id === id);
  if (!order) return toast("سفارش پیدا نشد.", true);
  modal(
    "بررسی سفارش",
    `کاربر: <span class="ltr">${e(order.user_id)}</span> · ${e(order.id)}`,
    `${summary(order)}<div class="summary-row"><span>وضعیت</span>${badge(order.status)}</div><div id="receipt-area">${order.has_receipt ? `<button class="btn btn-outline btn-full" data-action="view-receipt" data-id="${e(id)}">${icon("receipt")} مشاهدهٔ تصویر رسید</button>` : '<div class="support-note">هنوز رسیدی برای این سفارش ارسال نشده است.</div>'}</div>${order.status === "review" ? `<p class="modal-note">فقط پس از تطبیق مبلغ و زمان واریز با حساب مقصد، سفارش را تأیید کن. فعال‌سازی، یک کانفیگ در پنل می‌سازد یا همان اشتراک را تمدید می‌کند.</p><div class="modal-actions"><button class="btn btn-primary" data-action="approve-order" data-id="${e(id)}">${icon("check")} تأیید و فعال‌سازی</button><button class="btn btn-danger" data-action="reject-confirm" data-id="${e(id)}">رد رسید</button></div>` : ["needs_review", "provisioning"].includes(order.status) ? `<div class="review-warning">پاسخ پنل نامشخص است. ابتدا برچسب کاربر/سفارش، حجم و تاریخ را در HS Panel بررسی کن؛ کانفیگ دیگری نساز.</div><button class="btn btn-outline btn-full" data-action="recover-order" data-id="${e(id)}">بازیابی با شناسهٔ موجود پنل</button>` : ""}`,
  );
}
function recoveryModal(reference, trial = false) {
  modal(
    "بازیابی کانفیگ موجود",
    "بدون درخواست ساخت یا تمدید دوباره",
    `<div class="review-warning">ابتدا در HS Panel مالک، برچسب سفارش، حجم و انقضا را بررسی کن. فقط UUID کانفیگ صحیح را وارد کن. درخواست در حال پردازش تا ۵ دقیقه قابل بازیابی نیست.</div><form id="recovery-form" data-id="${e(reference)}" data-trial="${trial}"><div class="form-field"><label for="panel-uuid">شناسهٔ اشتراک در HS Panel</label><input id="panel-uuid" name="panel_id" dir="ltr" required maxlength="128" autocomplete="off" placeholder="UUID / Subscription ID"></div><div class="form-error" role="alert"></div><div class="form-footer"><button class="btn btn-primary" type="submit">بازیابی و ذخیره ${icon("check")}</button></div></form>`,
  );
}
function notifications() {
  const orders = state.data.orders.slice(0, 4);
  modal(
    "خبرهای اتصال تو",
    "آخرین وضعیت سفارش‌ها",
    `${orders.length ? orders.map((p) => `<div class="order-summary"><div class="summary-row"><strong>${e(p.plan_name)}</strong>${badge(p.status)}</div><small class="muted">${date(p.created_at)}</small></div>`).join("") : '<div class="modal-lead"><div class="modal-lead-icon">' + icon("bell") + "</div><h3>همه‌چیز آرومه!</h3><p>وقتی سفارشی ثبت کنی، وضعیتش رو اینجا می‌بینی.</p></div>"}<button class="btn btn-outline btn-full" data-action="modal-navigate" data-page="history">همهٔ سفارش‌ها ${icon("arrow")}</button>`,
  );
}

function renderGate() {
  const unauthorized =
    state.error?.code === "unauthorized" || !state.meta?.configured;
  const bot = chatURL(state.meta?.bot_username);
  document.getElementById("app").innerHTML =
    `<main id="main" class="gate-page"><section class="gate-card"><div class="gate-art"><img src="/static/assets/pingino-hero.webp" alt="پنگوئن پینگینو" width="285" height="285"></div><div class="gate-content"><h1>${unauthorized ? "پینگینو از تلگرام شروع می‌شه." : "اول به خانوادهٔ پینگینو بپیوند."}</h1><p>${unauthorized ? "برای استفادهٔ امن از فروشگاه و شناسایی حسابت، مینی‌اپ را از دکمهٔ داخل ربات تلگرام باز کن." : "برای استفاده از ربات، خرید کانفیگ و تست رایگان، اول عضو کانال پینگینو شو. فقط چند ثانیه زمان می‌بره."}</p>${unauthorized ? `${bot ? `<a class="btn btn-primary btn-full" href="${bot}" target="_blank" rel="noopener noreferrer">${icon("telegram")} ورود به ربات پینگینو</a>` : '<div class="info-banner"><p>مدیر باید توکن و نام کاربری ربات را تنظیم کند. این صفحه هنوز به یک ربات فعال وصل نشده است.</p></div>'}<button class="btn btn-outline btn-full" data-action="retry-session">دوباره بررسی کن ${icon("refresh")}</button>` : `<div class="gate-steps"><p><span class="step-num">۱</span> روی دکمهٔ زیر بزن و عضو کانال شو.</p><p><span class="step-num">۲</span> برگرد و «عضو شدم؛ بررسی کن» را بزن.</p></div><button class="btn btn-primary btn-full" data-action="channel">${icon("telegram")} عضویت در کانال پینگینو ${icon("upLeft")}</button><button class="btn btn-success btn-full" data-action="check-membership">${icon("checkCircle")} عضو شدم؛ بررسی کن</button>`}${state.error && state.error.code !== "unauthorized" && state.error.code !== "membership_required" ? `<div class="form-error" role="alert">${e(state.error.message)}</div>` : ""}<footer>🐧 پینگینو، یه دوست برای وصل موندن</footer></div></section></main>`;
}

async function refreshData() {
  state.data = await api("/session");
  if (state.page === "admin" && state.data.is_admin)
    state.admin = await api("/admin/overview");
}
async function navigate(page, category) {
  if (
    ![
      "home",
      "shop",
      "configs",
      "history",
      "help",
      "support",
      "admin",
    ].includes(page)
  )
    page = "home";
  closeModal();
  state.page = page;
  if (category) state.category = category;
  if (page !== "shop") state.renewal = null;
  history.replaceState(
    null,
    "",
    `#${page}${page === "shop" && state.category === "gaming" ? "/gaming" : ""}`,
  );
  shell();
  window.scrollTo({ top: 0, behavior: "instant" });
  if (tg?.initData) tg.HapticFeedback?.selectionChanged();
  if (page === "admin" && state.data.is_admin) {
    state.admin = await api("/admin/overview");
    shell();
  }
}

const actions = {
  navigate: (el) => {
    state.renewal = null;
    return navigate(el.dataset.page, el.dataset.category);
  },
  "modal-navigate": (el) => navigate(el.dataset.page),
  "close-modal": () => closeModal(),
  theme: () => {
    setTheme(
      document.documentElement.dataset.theme === "dark" ? "light" : "dark",
    );
    shell();
  },
  channel: () =>
    openLink(state.meta?.channel_url || "https://t.me/pingino_org"),
  refresh: (el) =>
    busy(el, async () => {
      await refreshData();
      shell();
      toast("همه‌چیز به‌روز شد.");
    }),
  notifications,
  "retry-session": (el) =>
    busy(el, async () => {
      state.meta = await api("/bootstrap");
      state.data = await api("/session");
      state.error = null;
      shell();
    }),
  "check-membership": (el) =>
    busy(el, async () => {
      state.data = await api("/membership/check", { method: "POST" });
      state.error = null;
      shell();
      toast("عضویتت تأیید شد؛ خوش اومدی!");
    }),
  category: (el) => {
    const category = el.dataset.category;
    if (
      state.renewal &&
      state.renewal.category !== category &&
      !el.dataset.admin
    )
      return toast("برای تمدید، یک پلن هم‌نوع کانفیگ فعلی انتخاب کن.", true);
    if (el.dataset.admin) state.adminCategory = category;
    else state.category = category;
    shell();
  },
  "select-plan": (el) => showPlan(el.dataset.id),
  "create-order": (el) =>
    busy(el, async () => {
      const data = await api("/orders", {
        method: "POST",
        body: {
          plan_id: state.pendingPlan,
          renewal_id: state.renewal?.id || null,
        },
      });
      state.renewal = null;
      await refreshData();
      shell();
      paymentModal(data);
    }),
  order: (el) =>
    busy(el, async () =>
      paymentModal(await api(`/orders/${encodeURIComponent(el.dataset.id)}`)),
    ),
  "copy-card": () =>
    copy(state.checkout.payment.card_number, "شمارهٔ کارت کپی شد."),
  "send-receipt": (el) =>
    busy(el, async () => {
      if (state.meta.demo) {
        await api(
          `/demo/orders/${encodeURIComponent(state.checkout.order.id)}/receipt`,
          { method: "POST" },
        );
        await refreshData();
        await navigate("history");
        toast("رسید آزمایشی ثبت شد؛ در پنل مدیریت قابل بررسی است.");
      } else openLink(state.checkout.receipt_url);
    }),
  "cancel-order": (el) =>
    busy(el, async () => {
      await api(`/orders/${encodeURIComponent(el.dataset.id)}/cancel`, {
        method: "POST",
      });
      await refreshData();
      await navigate("history");
      toast("سفارش لغو شد.");
    }),
  trial: () => trialModal(),
  "claim-trial": (el) =>
    busy(el, async () => {
      state.data = await api("/trial", { method: "POST" });
      await navigate("configs");
      toast(
        state.meta.demo
          ? "تست نمایشی ساخته شد؛ این لینک واقعی نیست."
          : "تستت آماده شد. یه روز مهمون ما باش!",
      );
    }),
  config: (el) => configModal(el.dataset.id),
  "copy-config": (el) => {
    const config = state.data.configs.find((c) => c.id === el.dataset.id);
    if (config?.config_link) return copy(config.config_link);
  },
  renew: (el) => {
    const cfg = state.data.configs.find((c) => c.id === el.dataset.id);
    if (!cfg?.renewable)
      return toast("این کانفیگ فعلاً قابل تمدید نیست.", true);
    state.renewal = cfg;
    return navigate("shop", cfg.category || "regular");
  },
  "cancel-renewal": () => {
    state.renewal = null;
    shell();
  },
  os: (el) => {
    state.os = el.dataset.os;
    shell();
  },
  "admin-tab": (el) => {
    state.adminTab = el.dataset.tab;
    shell();
  },
  "edit-plan": (el) => editPlanModal(el.dataset.id),
  "admin-order": (el) => adminOrderModal(el.dataset.id),
  "view-receipt": (el) =>
    busy(el, async () => {
      const blob = await api(
        `/admin/orders/${encodeURIComponent(el.dataset.id)}/receipt`,
      );
      if (receiptBlob) URL.revokeObjectURL(receiptBlob);
      receiptBlob = URL.createObjectURL(blob);
      document.getElementById("receipt-area").innerHTML =
        `<img class="receipt-preview" src="${receiptBlob}" alt="${state.meta.demo ? "رسید نمایشی، بدون پرداخت واقعی" : "تصویر رسید ارسال‌شده توسط کاربر"}">`;
    }),
  "approve-order": (el) =>
    busy(el, async () => {
      await api(`/admin/orders/${encodeURIComponent(el.dataset.id)}/approve`, {
        method: "POST",
      });
      await refreshData();
      closeModal();
      shell();
      toast(
        state.meta.demo
          ? "سفارش نمایشی تأیید و کانفیگ نمونه ساخته شد."
          : "سفارش تأیید و کانفیگ با موفقیت ذخیره شد.",
      );
    }),
  "reject-confirm": (el) =>
    modal(
      "این رسید رد شود؟",
      "فقط سفارش در انتظار بررسی بسته می‌شود.",
      `<p class="modal-note">پس از رد رسید، کاربر از نتیجه مطلع می‌شود. اگر از رد مطمئن نیستی، به بررسی سفارش برگرد.</p><div class="modal-actions"><button class="btn btn-danger" data-action="reject-order" data-id="${e(el.dataset.id)}">بله، رد رسید</button><button class="btn btn-outline" data-action="admin-order" data-id="${e(el.dataset.id)}">بازگشت به بررسی</button></div>`,
    ),
  "reject-order": (el) =>
    busy(el, async () => {
      await api(`/admin/orders/${encodeURIComponent(el.dataset.id)}/reject`, {
        method: "POST",
      });
      await refreshData();
      closeModal();
      shell();
      toast("رسید رد شد و وضعیت سفارش به‌روز شد.");
    }),
  "recover-order": (el) => recoveryModal(el.dataset.id),
  "recover-trial": (el) => recoveryModal(el.dataset.id, true),
};

document.addEventListener("click", async (event) => {
  const el = event.target.closest("[data-action]");
  if (!el || el.disabled || !actions[el.dataset.action]) return;
  event.preventDefault();
  try {
    await actions[el.dataset.action](el);
  } catch (error) {
    handleError(error);
  }
});
document.addEventListener("input", (event) => {
  if (event.target.id === "order-search") {
    state.search = event.target.value;
    document.getElementById("history-results").innerHTML = orderRows();
  }
});
document.addEventListener("change", (event) => {
  if (event.target.id === "order-filter") {
    state.historyFilter = event.target.value;
    document.getElementById("history-results").innerHTML = orderRows();
  }
});
document.addEventListener("submit", async (event) => {
  const form = event.target;
  if (
    !["edit-plan-form", "trial-settings-form", "recovery-form"].includes(
      form.id,
    )
  )
    return;
  event.preventDefault();
  const submit = form.querySelector("[type=submit]");
  form.querySelector(".form-error").textContent = "";
  try {
    await busy(submit, async () => {
      const fields = new FormData(form);
      if (form.id === "edit-plan-form") {
        await api(`/admin/plans/${encodeURIComponent(form.dataset.id)}`, {
          method: "PATCH",
          body: {
            name: fields.get("name"),
            price: cleanNumber(fields.get("price")),
            traffic_gb: cleanNumber(fields.get("traffic_gb")),
            days: cleanNumber(fields.get("days")),
            enabled: fields.has("enabled"),
          },
        });
      } else if (form.id === "trial-settings-form") {
        await api("/admin/trial", {
          method: "PATCH",
          body: {
            traffic_gb: cleanNumber(fields.get("traffic_gb")),
            category: fields.get("category"),
            enabled: fields.has("enabled"),
          },
        });
      } else {
        const path =
          form.dataset.trial === "true"
            ? `/admin/users/${encodeURIComponent(form.dataset.id)}/recover-trial`
            : `/admin/orders/${encodeURIComponent(form.dataset.id)}/recover`;
        await api(path, {
          method: "POST",
          body: { panel_id: fields.get("panel_id").trim() },
        });
      }
      await refreshData();
      closeModal();
      shell();
      toast("تغییرات ذخیره شد و بلافاصله در فروشگاه اعمال می‌شود.");
    });
  } catch (error) {
    if (
      [
        "unauthorized",
        "membership_required",
        "membership_unavailable",
      ].includes(error.code)
    )
      handleError(error);
    else form.querySelector(".form-error").textContent = error.message;
  }
});
document.getElementById("modal").addEventListener("click", (event) => {
  if (event.target === event.currentTarget) {
    const rect = event.currentTarget.getBoundingClientRect();
    if (
      event.clientX < rect.left ||
      event.clientX > rect.right ||
      event.clientY < rect.top ||
      event.clientY > rect.bottom
    )
      closeModal();
  }
});
document.getElementById("modal").addEventListener("close", () => {
  if (receiptBlob) {
    URL.revokeObjectURL(receiptBlob);
    receiptBlob = null;
  }
});
window.addEventListener("hashchange", () => {
  if (!state.data) return;
  const [page, category] = location.hash.slice(1).split("/");
  navigate(page || "home", category === "gaming" ? "gaming" : undefined).catch(
    handleError,
  );
});

(async function init() {
  if (tg?.initData) {
    tg.ready();
    tg.expand();
  }
  const [page, category] = location.hash.slice(1).split("/");
  state.page = [
    "home",
    "shop",
    "configs",
    "history",
    "help",
    "support",
    "admin",
  ].includes(page)
    ? page
    : "home";
  if (category === "gaming") state.category = "gaming";
  try {
    state.meta = await api("/bootstrap");
    state.data = await api("/session");
    if (state.page === "admin" && state.data.is_admin)
      state.admin = await api("/admin/overview");
    shell();
  } catch (error) {
    state.error = error;
    renderGate();
  }
})();
