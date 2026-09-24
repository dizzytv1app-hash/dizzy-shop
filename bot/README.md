# Dizzy Shop — Telegram Bot

Bu **alohida repo** — faqat Telegram bot (aiogram 3). API va Mini App boshqa-boshqa repolarda; bot ular bilan faqat HTTP orqali (backend API orqali) gaplashadi.

Admin panel butunlay shu botning ichida (`/admin`) — Mini Appda admin funksiyasi yo'q.

## Botning 3 asosiy qismi

1. **`/start`** — salomlashadi, "🛍️ Do'konni ochish" tugmasi bilan Mini Appni ochadi (`WEBAPP_URL`).
2. **`/help`** — foydalanuvchidan muammoni yozishni yoki rasm yuborishni so'raydi. Xabar:
   - to'g'ridan-to'g'ri barcha `ADMIN_IDS`ga Telegram xabari sifatida yuboriladi, **va**
   - backend API orqali PostgreSQL'ga saqlanadi (admin panelda ko'rinishi uchun).
3. **`/admin`** — faqat `ADMIN_IDS` ro'yxatidagi Telegram ID'lar uchun ochiladi:
   - 📊 Statistika, ➕ Mahsulot qo'shish (rasm→nom→narx→o'lcham→rang→qoldiq, **kategoriyasiz**), 📦 Mahsulotlar (tahrirlash/o'chirish/qidiruv), 🛒 Buyurtmalar (holat o'zgartirish), 💬 Yordam so'rovlari (javob yozish), 🏷️ Chegirmalar, 📢 Ilova ma'lumoti (birinchi ochilish/qo'llanma/do'kon haqida matnlari — bular Mini Appda ko'rinadi), ⚙️ Sozlamalar.

## O'rnatish

```bash
python -m venv venv
source venv/bin/activate   # Windowsda: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# .env: BOT_TOKEN, WEBAPP_URL, ADMIN_IDS, API_BASE_URL, BOT_API_SECRET
python -m app.main
```

`BOT_TOKEN` — @BotFather'dan. `ADMIN_IDS`ga o'z Telegram ID'ingizni yozish uchun botga `/start` bosing, so'ng masalan `@userinfobot`dan ID'ingizni bilib oling.

**Muhim:** `API_BASE_URL` — API repo qayerda ishlab turganiga ishora qilsin (masalan `http://localhost:8000/api` yoki production manzili). `BOT_API_SECRET` — API repo'dagi `.env`da ham **bir xil** bo'lishi shart, aks holda bot admin so'rovlari rad etiladi.

## Bot API'dan nimani kutadi

To'liq endpoint ro'yxati va JSON shakllari — API repo'sining README.md faylida (`app/routers/`). Bot chaqiradigan asosiy endpointlar: `/admin/products`, `/admin/orders`, `/admin/discounts`, `/admin/support`, `/admin/stats`, `/admin/content/{key}`, `/support`.

## Production deploy

Railway/VPS kabi Python doimiy ishlaydigan xizmatga: `python -m app.main` (polling rejimida ishlaydi, webhook shart emas).
