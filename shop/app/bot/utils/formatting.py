def fmt_price(amount: int) -> str:
    return f"{amount:,}".replace(",", " ") + " so'm"


def product_card_text(product) -> str:
    lines = [f"🏷 <b>{product.name}</b>", f"Kodi: <code>{product.code}</code>"]
    if product.has_discount:
        lines.append(f"Narxi: <s>{fmt_price(product.old_price)}</s>  ➜  <b>{fmt_price(product.price)}</b>"
                      f"  (-{product.discount_percent}%)")
    else:
        lines.append(f"Narxi: <b>{fmt_price(product.price)}</b>")

    colors = ", ".join(c.name + ("" if c.is_available else " (mavjud emas)") for c in product.colors) or "—"
    sizes = ", ".join(s.name + ("" if s.is_available else " (mavjud emas)") for s in product.sizes) or "—"
    lines.append(f"Ranglar: {colors}")
    lines.append(f"O'lchamlar: {sizes}")
    lines.append(f"Rasmlar soni: {len(product.images)}")
    lines.append(f"Holati: {'✅ faol' if product.is_active else '🚫 o‘chirilgan'}")
    return "\n".join(lines)


def order_card_text(order) -> str:
    from app.models import OrderStatus
    user = order.user
    user_link = f"@{user.username}" if user and user.username else f"id:{user.telegram_id}" if user else "—"
    lines = [
        f"📦 Buyurtma <code>{order.order_number}</code>",
        f"Holati: {OrderStatus.label(order.status)}",
        f"Mijoz: {user_link} ({user.full_name or ''})",
        f"Mahsulot: {order.product_name} ({order.product_code})",
        f"Rang: {order.color} | O'lcham: {order.size}",
        f"Narx: {fmt_price(order.price)}",
    ]
    if order.prepay_amount:
        lines.append(f"Oldindan to'lov (50%): {fmt_price(order.prepay_amount)}")
    return "\n".join(lines)
