"""
Bot shu fayl orqali umumiy backend (PostgreSQL ustidagi API) bilan gaplashadi.
Xuddi shu backend mini appga ham xizmat qiladi — shuning uchun bot orqali
qilingan har bir o'zgarish (mahsulot, chegirma, matn) darhol mini appda ham
ko'rinadi.

Admin so'rovlarida ikkita header yuboriladi:
  X-Bot-Secret — API .env dagi BOT_API_SECRET bilan bir xil
  X-Admin-Id   — buyruq yuborgan adminning Telegram ID'si
"""

import httpx

from app.config import settings


class ApiError(Exception):
    def __init__(self, status: int, detail: str):
        self.status = status
        self.detail = detail
        super().__init__(f"API xato ({status}): {detail}")


def _admin_headers(admin_id: int) -> dict:
    return {"X-Bot-Secret": settings.BOT_API_SECRET, "X-Admin-Id": str(admin_id)}


async def _request(method: str, path: str, admin_id: int | None = None, **kwargs) -> dict:
    headers = _admin_headers(admin_id) if admin_id else {}
    url = f"{settings.API_BASE_URL}{path}"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.request(method, url, headers=headers, **kwargs)
    if resp.status_code >= 400:
        raise ApiError(resp.status_code, resp.text)
    return resp.json() if resp.content else {}


# ---- Mahsulotlar ----

async def create_product(admin_id: int, data: dict) -> dict:
    return await _request("POST", "/admin/products", admin_id=admin_id, json=data)


async def update_product(admin_id: int, product_id: int, data: dict) -> dict:
    return await _request("PUT", f"/admin/products/{product_id}", admin_id=admin_id, json=data)


async def delete_product(admin_id: int, product_id: int) -> dict:
    return await _request("DELETE", f"/admin/products/{product_id}", admin_id=admin_id)


async def list_products(admin_id: int, page: int = 0, limit: int = 6, search: str | None = None) -> dict:
    params = {"page": page, "limit": limit}
    if search:
        params["search"] = search
    return await _request("GET", "/admin/products", admin_id=admin_id, params=params)


# ---- Buyurtmalar ----

async def list_orders(admin_id: int, page: int = 0, limit: int = 6) -> dict:
    return await _request("GET", "/admin/orders", admin_id=admin_id, params={"page": page, "limit": limit})


async def set_order_status(admin_id: int, order_id: int, status: str) -> dict:
    return await _request("PUT", f"/admin/orders/{order_id}/status", admin_id=admin_id, json={"status": status})


# ---- Chegirmalar ----

async def create_discount(admin_id: int, data: dict) -> dict:
    return await _request("POST", "/admin/discounts", admin_id=admin_id, json=data)


async def list_discounts(admin_id: int) -> dict:
    return await _request("GET", "/admin/discounts", admin_id=admin_id)


async def toggle_discount(admin_id: int, discount_id: int, active: bool) -> dict:
    return await _request("PUT", f"/admin/discounts/{discount_id}", admin_id=admin_id, params={"active": active})


async def delete_discount(admin_id: int, discount_id: int) -> dict:
    return await _request("DELETE", f"/admin/discounts/{discount_id}", admin_id=admin_id)


# ---- Statistika ----

async def get_stats(admin_id: int) -> dict:
    return await _request("GET", "/admin/stats", admin_id=admin_id)


# ---- Yordam so'rovlari ----

async def create_support_ticket(user_id: int, username: str | None, message: str, photo_file_id: str | None) -> dict:
    return await _request(
        "POST", "/support",
        json={"user_id": user_id, "username": username, "message": message, "photo_file_id": photo_file_id},
    )


async def list_support_tickets(admin_id: int, page: int = 0, limit: int = 6, status: str | None = None) -> dict:
    params = {"page": page, "limit": limit}
    if status:
        params["status"] = status
    return await _request("GET", "/admin/support", admin_id=admin_id, params=params)


async def reply_support_ticket(admin_id: int, ticket_id: int, reply: str | None = None, status: str | None = None) -> dict:
    payload = {}
    if reply:
        payload["reply"] = reply
    if status:
        payload["status"] = status
    return await _request("POST", f"/admin/support/{ticket_id}/reply", admin_id=admin_id, json=payload)


# ---- Ilova matnlari (onboarding / guide / shop_info) ----

async def get_content(key: str) -> dict:
    return await _request("GET", f"/content/{key}")


async def update_content(admin_id: int, key: str, value: str) -> dict:
    return await _request("PUT", f"/admin/content/{key}", admin_id=admin_id, json={"value": value})
