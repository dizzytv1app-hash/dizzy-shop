from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends

from app.database import get_db
from app.auth import require_admin
from app.models import Content
from app.schemas import ContentUpdate

router = APIRouter(tags=["content"])

DEFAULTS = {
    "onboarding": (
        "Dizzy Shop'ga xush kelibsiz! 🛍️\n\n"
        "Bu yerda kiyim, anime, gaming, streetwear, poyabzal va aksessuarlarni topasiz. "
        "Mahsulotlar doimiy yangilanib turadi. Sevimlilarga qo'shishingiz, savatga solishingiz "
        "va demo buyurtma berishingiz mumkin. Batafsil — Profil → Qo'llanma."
    ),
    "guide": (
        "📖 Qo'llanma\n\n"
        "1. Katalogdan yoki qidiruv orqali mahsulot toping.\n"
        "2. Mahsulotni ochib, o'lcham va rangni tanlang.\n"
        "3. ❤️ tugmasi bilan sevimlilarga qo'shing.\n"
        "4. 🛒 Savatga qo'shish tugmasini bosing.\n"
        "5. Savatda \"Buyurtma berish\"ni bosing — demo buyurtma yaratiladi.\n"
        "6. Profil → Buyurtmalarim bo'limida holatini kuzating.\n"
        "7. Muammo bo'lsa, botda /help yozing."
    ),
    "shop_info": "Dizzy Shop — zamonaviy demo kiyim-kechak do'koni.",
}


@router.get("/content/{key}")
def get_content(key: str, db: Session = Depends(get_db)):
    row = db.get(Content, key)
    return {"key": key, "value": row.value if row else DEFAULTS.get(key, "")}


@router.put("/admin/content/{key}")
def update_content(key: str, data: ContentUpdate, db: Session = Depends(get_db), _admin: int = Depends(require_admin)):
    row = db.get(Content, key)
    if row:
        row.value = data.value
    else:
        row = Content(key=key, value=data.value)
        db.add(row)
    db.commit()
    return {"ok": True}
