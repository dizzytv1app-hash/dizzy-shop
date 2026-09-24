from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.config import settings
from app.routers import products, users, favorites, cart, orders, discounts, help as help_router, content, stats, files

app = FastAPI(title=f"{settings.SHOP_NAME} API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    # Demo/dastlabki ishga tushirish uchun. Real production'da Alembic migratsiyalaridan foydalaning.
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok", "shop": settings.SHOP_NAME}


app.include_router(products.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(favorites.router, prefix="/api")
app.include_router(cart.router, prefix="/api")
app.include_router(orders.router, prefix="/api")
app.include_router(discounts.router, prefix="/api")
app.include_router(help_router.router, prefix="/api")
app.include_router(content.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(files.router, prefix="/api")
