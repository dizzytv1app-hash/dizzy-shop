# Dizzy Shop — API (Bot, Mini App va PostgreSQL o'rtasidagi qatlam)

FastAPI + PostgreSQL. Bot va Mini App ikkalasi ham shu API orqali bitta bazaga ulanadi.

## O'rnatish

```bash
cd api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# .env: DATABASE_URL, BOT_TOKEN, ADMIN_IDS, BOT_API_SECRET, CORS_ORIGINS
```

## PostgreSQL

```bash
# lokal misol (Docker bilan):
docker run --name dizzy-pg -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=dizzy_shop -p 5432:5432 -d postgres:16
```

`DATABASE_URL` shu bazaga ishora qilsin: `postgresql://postgres:postgres@localhost:5432/dizzy_shop`

Ishga tushganda jadval (tablo)lar avtomatik yaratiladi (`Base.metadata.create_all`). Bu demo/boshlang'ich holat uchun yetarli; real production'da Alembic migratsiyalariga o'ting.

## Ishga tushirish

```bash
uvicorn app.main:app --reload --port 8000
```

Tekshirish: `GET http://localhost:8000/health`

## Autentifikatsiya

- **Admin (bot):** har bir `/api/admin/...` so'roviga `X-Bot-Secret` va `X-Admin-Id` headerlari kerak (bot avtomatik qo'shadi).
- **Foydalanuvchi (mini app):** `X-Telegram-Init-Data` header — Telegram `WebApp.initData` qiymati. Server buni bot tokeni bilan HMAC-SHA256 orqali tekshiradi (`app/auth.py`). Frontenddan kelgan Telegram ID'ga hech qachon to'g'ridan-to'g'ri ishonilmaydi.

## Asosiy endpointlar

| | Public (mini app) | Admin (bot) |
|---|---|---|
| Mahsulotlar | `GET /api/products`, `GET /api/products/{id}` | `POST/PUT/DELETE /api/admin/products`, `GET /api/admin/products` |
| Sevimlilar | `GET/POST/DELETE /api/favorites` | — |
| Savat | `GET/POST/PUT/DELETE /api/cart` | — |
| Buyurtmalar | `POST /api/orders` (checkout), `GET /api/orders` | `GET /api/admin/orders`, `PUT /api/admin/orders/{id}/status` |
| Chegirmalar | `GET /api/discounts` | `POST/PUT/DELETE /api/admin/discounts` |
| Yordam so'rovi | `POST /api/support` (bot chaqiradi) | `GET /api/admin/support`, `POST /api/admin/support/{id}/reply` |
| Matnlar | `GET /api/content/{key}` | `PUT /api/admin/content/{key}` |
| Statistika | — | `GET /api/admin/stats` |
| Rasm | `GET /api/files/{file_id}` (Telegram rasmini xavfsiz oqim qiladi) | — |

## Xavfsizlik eslatmalari

- Bot tokeni frontendga hech qachon chiqmaydi — hatto rasm ko'rsatishda ham (`/api/files/{id}` server orqali stream qiladi, redirect qilmaydi).
- `BOT_API_SECRET` faqat bot va API o'rtasida — mini app buni bilmaydi va ishlatmaydi.
- CORS faqat `CORS_ORIGINS`da ko'rsatilgan domenlardan so'rovlarga ruxsat beradi (production'da `*` ishlatmang).
