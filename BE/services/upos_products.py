"""
services/upos_products.py
Tìm kiếm sản phẩm từ UPOS API, xử lý 0/1/nhiều kết quả.
"""
import re
import config
from services.upos_auth import call_with_auth


def search_product(query: str = "", size: str = "", color: str = "") -> str:
    """
    Tìm sản phẩm theo từ khóa/size/màu từ UPOS API.
    Trả về string mô tả kết quả để inject vào context của Miko.
    """
    print(f"\n[upos_products] Đang gọi API: {config.UPOS_SEARCH_PRODUCT_URL}")
    resp = call_with_auth("GET", config.UPOS_SEARCH_PRODUCT_URL)
    
    print(f"[upos_products] Status code: {resp.status_code}")

    if resp.status_code != 200:
        print(f"[upos_products] Lỗi API: {resp.text}")
        return f"[Hệ thống lỗi khi tìm sản phẩm: HTTP {resp.status_code}]"

    body = resp.json()
    print(f"[upos_products] Response data length: {len(str(body))} bytes")
    # Uncomment dòng dưới nếu muốn in chi tiết toàn bộ body (rất dài)
    # print(f"[upos_products] Raw body: {body}")

    # Xử lý nhiều cấu trúc response UPOS có thể trả về
    raw_items: list = []
    if isinstance(body.get("data"), list):
        raw_items = body["data"]
    elif isinstance(body.get("data"), dict):
        raw_items = body["data"].get("items", body["data"].get("data", []))
    elif isinstance(body, list):
        raw_items = body

    # ── Filter phía BE theo query / size / color ──
    keywords = [k.lower() for k in query.split() if k] if query else []
    size_kw = size.strip().upper() if size else ""
    color_kw = _normalize_color(color) if color else ""

    matched = []
    for item in raw_items:
        name = str(item.get("name", "") or item.get("product_name", "")).lower()
        item_sizes = str(item.get("sizes", "") or item.get("size", "")).upper()
        item_colors = _normalize_color(str(item.get("colors", "") or item.get("color", "")))
        item_status = str(item.get("status", "1"))

        # Bỏ qua sản phẩm ngừng bán / hết hàng (chỉ chấp nhận status '1' - Active)
        if item_status != "1":
            continue

        # Lọc theo keyword tên sản phẩm (phải chứa ĐẦY ĐỦ các từ khóa - logic AND)
        if keywords and not all(kw in name for kw in keywords):
            continue

        # Lọc theo size
        if size_kw and size_kw not in item_sizes:
            continue

        # Lọc theo màu
        if color_kw and color_kw not in item_colors:
            continue

        matched.append(item)

    # In chi tiết các sản phẩm khớp sau khi lọc để debug dễ dàng trên Console
    print(f"[upos_products] Số lượng sản phẩm khớp: {len(matched)}")
    for idx, item in enumerate(matched[:10]):
        name = item.get("product_name") or item.get("name")
        price = item.get("price") or item.get("sell_price")
        colors = item.get("color") or item.get("colors")
        sizes = item.get("size") or item.get("sizes")
        status = item.get("status")
        print(f"  {idx+1}. {name} | Giá: {price} | Màu: {colors} | Size: {sizes} | Status: {status}")

    return _format_results(matched), matched[:5]


def _normalize_color(text: str) -> str:
    """Chuẩn hoá màu sắc về lowercase không dấu để so sánh."""
    text = text.lower()
    replacements = {
        "đen": "den", "trắng": "trang", "đỏ": "do", "xanh": "xanh",
        "vàng": "vang", "cam": "cam", "tím": "tim", "hồng": "hong",
        "nâu": "nau", "xám": "xam", "be": "be",
    }
    for vn, en in replacements.items():
        text = text.replace(vn, en)
    return text


def _format_results(items: list) -> str:
    """Định dạng kết quả tìm kiếm thành string cho Miko đọc."""
    if not items:
        return "[KẾT QUẢ TÌM KIẾM: Không tìm thấy sản phẩm phù hợp với yêu cầu của khách.]"

    if len(items) == 1:
        item = items[0]
        name = item.get("name") or item.get("product_name", "Không rõ")
        price = _fmt_price(item.get("price") or item.get("sell_price"))
        sizes = item.get("sizes") or item.get("size", "Liên hệ để biết thêm")
        colors = item.get("colors") or item.get("color", "Liên hệ để biết thêm")
        sku = item.get("sku", "")
        return (
            f"[KẾT QUẢ TÌM KIẾM — 1 sản phẩm]\n"
            f"Tên: {name}\n"
            f"Giá: {price}\n"
            f"Size có sẵn: {sizes}\n"
            f"Màu có sẵn: {colors}\n"
            f"SKU: {sku}"
        )

    # Nhiều sản phẩm — liệt kê ngắn, tối đa 5
    lines = [f"[KẾT QUẢ TÌM KIẾM — {len(items)} sản phẩm (hiển thị tối đa 5)]"]
    for i, item in enumerate(items[:5], 1):
        name = item.get("name") or item.get("product_name", "Không rõ")
        price = _fmt_price(item.get("price") or item.get("sell_price"))
        lines.append(f"{i}. {name} — {price}")
    if len(items) > 5:
        lines.append(f"...và {len(items) - 5} sản phẩm khác.")
    return "\n".join(lines)


def _fmt_price(price) -> str:
    """Format giá tiền VNĐ."""
    try:
        return f"{int(price):,}đ".replace(",", ".")
    except (TypeError, ValueError):
        return "Liên hệ để biết giá"
