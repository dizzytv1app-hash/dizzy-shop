"""
Bu - kelajakdagi web-sayt/Mini App ulanadigan backend API skeleti.
Web-sayt hali yaratilmagan, lekin bot bilan BITTA bazadan foydalanish uchun
asos shu yerda tayyor turibdi: web-sayt tayyor bo'lganda shu endpointlar
kengaytiriladi (buyurtma yaratish, Telegram initData tekshirish va h.k.)
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.database import get_session
from app.services.products import get_product_by_code, list_products

app = FastAPI(title="Kiyim do'koni API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Web-sayt domeni aniqlangach shu yerga faqat o'sha domenni yozish tavsiya etiladi
    allow_methods=["*"],
    allow_headers=["*"],
)


def _product_to_dict(p) -> dict:
    return {
        "code": p.code,
        "name": p.name,
        "price": p.price,
        "old_price": p.old_price,
        "discount_percent": p.discount_percent,
        "colors": [{"name": c.name, "available": c.is_available} for c in p.colors],
        "sizes": [{"name": s.name, "available": s.is_available} for s in p.sizes],
        "images": [img.file_id for img in p.images],
    }


@app.get("/api/products")
def api_list_products():
    with get_session() as db:
        products = list_products(db, active_only=True)
        return [_product_to_dict(p) for p in products]


@app.get("/api/products/{code}")
def api_get_product(code: str):
    with get_session() as db:
        product = get_product_by_code(db, code, active_only=True)
        if not product:
            raise HTTPException(status_code=404, detail="Mahsulot topilmadi")
        return _product_to_dict(product)


# TODO (web-sayt yaratilganda qo'shiladi):
# - POST /api/orders  (Telegram WebApp initData'ni tekshirib, buyurtma yaratish)
# - Rasmlarni ko'rsatish uchun Telegram file_id'larni haqiqiy URL'ga aylantiruvchi endpoint
#   yoki rasmlarni alohida joyga (masalan S3/CDN) yuklab qo'yish logikasi
