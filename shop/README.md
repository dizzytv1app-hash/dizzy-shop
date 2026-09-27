# Kiyim do'koni — Telegram bot + Backend (Web-sayt uchun asos)

Bu loyiha ikki qismdan iborat, lekin **BITTA umumiy baza va BITTA services (biznes-logika)
qatlamidan** foydalanadi:

- `app/bot/` — Telegram bot (aiogram 3). To'liq ishlaydi.
- `app/api/` — kelajakdagi web-sayt uchun backend (FastAPI). Hozircha faqat mahsulotlarni
  ko'rsatish endpointlari bor (`GET /api/products`, `GET /api/products/{code}`). Web-sayt
  o'zi hali yaratilmagan — buyurtma sahifasi tayyor bo'lganda shu API kengaytiriladi.

Ma'lumotlar bazasi: SQLite (`shop.db` fayli, avtomatik yaratiladi).

---

## 1. O'rnatish

```bash
cd shop
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Sozlash

`.env.example` faylidan nusxa oling:

```bash
cp .env.example .env
```

`.env` faylini oching va to'ldiring:

| O'zgaruvchi | Izoh |
|---|---|
| `BOT_TOKEN` | @BotFather'dan `/newbot` orqali olingan token |
| `OWNER_TELEGRAM_ID` | Sizning shaxsiy Telegram ID raqamingiz. Bilish uchun @userinfobot ga `/start` bosing. Bot birinchi marta ishga tushganda sizni avtomatik "bot egasi" (asosiy admin) qiladi |
| `WEBSITE_URL` | Hozircha bo'sh qoldiring. Sayt tayyor bo'lib hostga qo'yilgach, shu yerga to'liq manzilni yozasiz (masalan `https://mystore.uz`) |
| `DATABASE_URL` | O'zgartirish shart emas |

## 3. Botni ishga tushirish

```bash
python run_bot.py
```

Konsolda `Bot ishga tushmoqda...` chiqsa — ishladi. Telegram'da botga `/start` yuboring.

`/admin` buyrug'i faqat `.env` dagi `OWNER_TELEGRAM_ID` uchun ishlaydi (birinchi marta).
Keyinchalik admin panelidan yangi adminlar qo'shishingiz mumkin.

## 4. Kerakli boshlang'ich sozlashlar (bot ichida, admin panelida)

Bot ishga tushgandan keyin `/admin` orqali quyidagilarni sozlang:

1. **💬 Help chatini ulash** — botni biror guruhga admin qilib qo'shing, guruh ID'sini
   (masalan `@getmyid_bot` yoki `@userinfobot` yordamida) bot orqali kiriting.
2. **📤 Kanalga yuborish** — xuddi shunday, kanalni ham botga admin qilib qo'shib, ID'sini kiriting.
3. **💳 Karta sozlash** — to'lov uchun karta raqami va egasining F.I.SH'ini kiriting.
4. **➕ Kiyim qo'shish** orqali birinchi mahsulotingizni qo'shing.

Shundan keyin barcha funksiyalar (buyurtmalar, chegirmalar, statistika) to'liq ishlaydi.

## 5. API'ni ishga tushirish (ixtiyoriy, web-sayt yaratilganda kerak bo'ladi)

```bash
python run_api.py
```

`http://localhost:8000/api/products` orqali mahsulotlar ro'yxatini JSON ko'rinishida
ko'rishingiz mumkin — bu web-sayt qurilganda ishlatiladigan endpoint.

---

## Loyiha tuzilishi

```
shop/
├── app/
│   ├── config.py            # .env orqali sozlamalar
│   ├── database.py          # SQLAlchemy ulanish (bitta umumiy baza)
│   ├── models.py            # Barcha jadvallar
│   ├── services/            # Biznes-logika (bot VA API shu yerdan foydalanadi)
│   │   ├── users.py
│   │   ├── products.py
│   │   ├── orders.py
│   │   ├── help.py
│   │   ├── settings_service.py
│   │   └── stats.py
│   ├── bot/
│   │   ├── main.py          # Bot entrypoint, barcha routerlarni ulaydi
│   │   ├── keyboards.py
│   │   ├── states.py
│   │   └── handlers/
│   │       ├── user/        # start, help, buyurtma berish, to'lov
│   │       └── admin/       # kiyim qo'shish/boshqarish, chegirma, admin, sozlama,
│   │                        # kanalga yuborish, buyurtmalar, statistika, kod qidirish
│   └── api/
│       └── main.py          # Kelajakdagi web-sayt uchun FastAPI skeleti
├── run_bot.py
├── run_api.py
├── requirements.txt
└── .env.example
```

## Nima to'liq ishlaydi

- Mahsulot qo'shish/tahrirlash/o'chirish (soft-delete — tarixiy buyurtmalar buzilmaydi)
- Rang/o'lchamni alohida "mavjud/mavjud emas" qilib belgilash
- Chegirma qo'yish — foiz avtomatik hisoblanadi, olib tashlash
- To'liq buyurtma jarayoni: mijoz tanlaydi → admin qabul qiladi (50% oldindan to'lov
  ko'rsatiladi) → mijoz chek yuboradi → **faqat admin tasdiqlagach** to'lov tasdiqlangan
  hisoblanadi → yetkazish holatlari → yetkazildi
- Kanalga post + "Buyurtma berish" tugmasi (deep-link orqali botni ochadi va xuddi shu
  buyurtma jarayonini boshlaydi)
- Admin huquqlari **server (bot) tomonida** tekshiriladi — mijoz hech qanday buyruq bilan
  aylanib o'ta olmaydi
- Statistika — real bazadan hisoblanadi, bekor qilingan/tasdiqlanmagan buyurtmalar savdoga
  qo'shilmaydi
- `/help` — 5 soatlik limit, matn+rasm, help-chatga profil havolasi bilan yuboriladi

## Hali qilinmagan / keyingi qadamlar

- **Web-sayt (frontend)** — hali yaratilmadi, siz alohida so'raganingiz uchun navbatda.
  Backend (`app/api/main.py`) shunga tayyor asos sifatida qurilgan.
- **Telegram Mini App uchun avtorizatsiya** (`initData` tekshirish) — web-sayt qurilganda
  qo'shiladi.
- Rasmlarni websaytda ko'rsatish uchun Telegram `file_id`'larni haqiqiy rasm URL'iga
  aylantirish kerak bo'ladi (bot API orqali yoki alohida CDN'ga yuklab).

## Muhim ogohlantirish (halollik uchun)

Ushbu muhitda internetga chiqish imkoni yo'qligi sababli, kodni haqiqiy Telegram serveri
bilan ishga tushirib sinab ko'rish imkonim bo'lmadi. Barcha fayllarning **Python sintaksisi
tekshirilgan va xatosiz**, arxitektura va mantiq diqqat bilan qurilgan, lekin birinchi marta
o'zingiz ishga tushirganda mayda xatoliklar (masalan kutilmagan holat) chiqishi mumkin —
xato matnini yuborsangiz, tezda tuzataman.
