"""
Admin mahsulot qo'shganda kategoriya so'ralmaydi (talab shunday).
Lekin mini app katalogida 6 ta bo'lim bor — shuning uchun mahsulot nomi
bo'yicha kalit so'zlarga qarab avtomatik kategoriya aniqlanadi.
Moslashtirish kerak bo'lsa — shu ro'yxatlarni to'ldirish kifoya.
"""

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "anime": ["anime", "naruto", "manga", "titan", "goku", "luffy", "chibi", "otaku"],
    "gaming": ["gaming", "game", "gamer", "playstation", "xbox", "esports", "pixel", "controller"],
    "streetwear": ["streetwear", "oversize", "hoodie", "cargo", "bomber", "street"],
    "shoes": ["krossovka", "poyabzal", "shoe", "sneaker", "botinka", "tufli"],
    "accessories": ["aksessuar", "sumka", "kepka", "shapka", "soat", "zanjir", "sumka", "ko'zoynak", "belbog"],
}

CATEGORY_LABELS: dict[str, str] = {
    "clothing": "👕 Kiyim",
    "anime": "🎌 Anime",
    "gaming": "🎮 Gaming",
    "streetwear": "🖤 Streetwear",
    "shoes": "👟 Poyabzal",
    "accessories": "🧢 Aksessuar",
}

DEFAULT_CATEGORY = "clothing"


def classify_product(name: str) -> str:
    lowered = name.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in lowered for kw in keywords):
            return category
    return DEFAULT_CATEGORY
