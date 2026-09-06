# Telegram Bot - فروش کانفیگ HS Panel

## نصب

```bash
cd bot
pip install -r requirements.txt
```

## تنظیم `config.json`

```json
{
  "bot_token": "توکن ربات از @BotFather",
  "panel_url": "آدرس پنل HS (مثلاً https://panel.domain.com)",
  "panel_password": "رمز پنل",
  "admin_ids": [123456789],
  "card_number": "6037-0000-0000-0000",
  "card_name": "نام صاحب کارت",
  "support_username": "یوزرنیم پشتیبانی"
}
```

### پیدا کردن آیدی عددی تلگرام
به [@userinfobot](https://t.me/userinfobot) پیام دهید.

## اجرا

```bash
python bot.py
```

## ساختار فایل‌ها

```
bot/
├── bot.py          # فایل اصلی ربات
├── panel_api.py    # کلاینت API پنل
├── config.json     # تنظیمات
├── users.json      # اطلاعات کاربران (خودکار)
├── pending_payments.json  # پرداخت‌ها (خودکار)
├── receipts/       # رسیدهای پرداخت (خودکار)
├── requirements.txt
└── README.md
```

## امکانات

- خرید کانفیگ با چند پلن (ماهانه/سه‌ماهه/سالانه)
- تأیید پرداخت توسط ادمین
- تمدید کانفیگ
- ارسال همگانی
- آمار کامل ادمین
- اتصال خودکار به پنل HS
