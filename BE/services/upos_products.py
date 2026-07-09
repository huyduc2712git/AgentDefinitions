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
    if isinstance(body, dict):
        if isinstance(body.get("data"), list):
            raw_items = body["data"]
        elif isinstance(body.get("data"), dict):
            raw_items = body["data"].get("items", body["data"].get("data", body["data"].get("docs", [])))
        elif isinstance(body.get("items"), list):
            raw_items = body["items"]
    elif isinstance(body, list):
        raw_items = body

    print(f"[upos_products] Số lượng raw_items: {len(raw_items)}")
    if len(raw_items) > 0:
        first_item = raw_items[0]
        print(f"[upos_products] First item keys: {list(first_item.keys())[:10]}")
        print(f"[upos_products] First item status: {first_item.get('status')} (type: {type(first_item.get('status'))})")
    elif isinstance(body, dict):
        print(f"[upos_products] Body keys: {body.keys()}")
        if "data" in body and isinstance(body["data"], dict):
            print(f"[upos_products] Body['data'] keys: {body['data'].keys()}")

    # ── Filter phía BE theo query / size / color ──
    # Tách từ khóa thành các TỪ thực sự (loại bỏ dấu câu như '-')
    raw_keywords = re.findall(r'\w+', query.lower()) if query else []
    
    # Loại bỏ các từ vô nghĩa hoặc đại từ thường gặp trong câu hỏi tự nhiên
    stop_words = {
        "shop", "mình", "có", "sản", "phẩm", "gì", "nào", "những", "cái", "bán", "cho", "xem",
        "hiện", "tại", "đang", "thì", "vậy", "nhé", "nha", "ạ", "ơi", "muốn", "tìm", "mua",
        "cần", "hỏi", "về", "để", "lại", "với", "được", "không", "nhỉ", "đây", "rồi", "này",
        "kia", "ấy", "ở", "trong", "ngoài", "anh", "chị", "em", "bạn", "chào", "tôi", "chi", "tiết", "đi",
        "một", "hai", "ba", "bốn", "năm", "1", "2", "3", "4", "5", "số", "vài", "các", "xin", "lấy", "thôi",
        "mấy", "chút", "thử", "của", "từ", "đến", "là", "thêm"
    }
    keywords = set(k for k in raw_keywords if k not in stop_words)
    size_kw = size.strip().upper() if size else ""
    color_kw = _normalize_color(color) if color else ""

    scored_items = []
    for item in raw_items:
        name = str(item.get("name", "") or item.get("product_name", "")).lower()
        item_sizes = str(item.get("sizes", "") or item.get("size", "")).upper()
        item_colors = _normalize_color(str(item.get("colors", "") or item.get("color", "")))
        item_status = str(item.get("status", "1"))

        # Bỏ qua sản phẩm ngừng bán / hết hàng (chỉ chấp nhận status '1' - Active)
        if item_status != "1":
            continue

        # Lọc theo keyword: Tính điểm số từ khóa khớp bằng giao tập các TỪ (word intersection)
        score = 0
        if keywords:
            name_words = set(re.findall(r'\w+', name))
            matched_kws = keywords.intersection(name_words)
            score = len(matched_kws)
            # Nếu có từ khóa nhưng không khớp bất kỳ từ nào -> bỏ qua sản phẩm này
            if score == 0:
                continue

        # Lọc theo size
        if size_kw:
            in_field = item_sizes != "NONE" and size_kw in item_sizes
            in_name = bool(re.search(rf"\b{re.escape(size_kw)}\b", name.upper()))
            if not (in_field or in_name):
                continue

        # Lọc theo màu
        if color_kw:
            in_field = item_colors != "NONE" and color_kw in item_colors
            normalized_name = _normalize_color(name)
            in_name = color_kw in normalized_name
            if not (in_field or in_name):
                continue

        scored_items.append((score, item))

    # Sắp xếp sản phẩm theo điểm số từ khóa (khớp nhiều từ khóa nhất lên đầu)
    scored_items.sort(key=lambda x: x[0], reverse=True)
    
    # CHỈ giữ lại những sản phẩm có điểm số cao nhất (tránh trả về các sản phẩm ít liên quan hơn)
    if scored_items:
        max_score = scored_items[0][0]
        matched = [item for score, item in scored_items if score == max_score]
    else:
        matched = []
    # Nhóm các sản phẩm trùng tên gốc (trước dấu '-') để không trả về 1 loạt biến thể giống nhau
    unique_base_names = set()
    filtered_matched = []
    for item in matched:
        name = str(item.get("name", "") or item.get("product_name", ""))
        base_name = name.split('-')[0].strip().lower()
        if base_name not in unique_base_names:
            unique_base_names.add(base_name)
            filtered_matched.append(item)
    matched = filtered_matched

    # Nếu tìm thấy nhiều sản phẩm, ưu tiên các sản phẩm khớp hoàn toàn với chuỗi query gốc
    if len(matched) > 1 and query:
        def clean_str(s: str) -> str:
            s = s.lower()
            return re.sub(r'[^a-z0-9àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]', '', s)
        clean_query = clean_str(query)
        exact_matches = []
        for item in matched:
            item_name = str(item.get("name", "") or item.get("product_name", ""))
            if clean_str(item_name) == clean_query:
                exact_matches.append(item)
        if exact_matches:
            matched = exact_matches

    # In chi tiết các sản phẩm khớp sau khi đã deduplicate để debug dễ dàng trên Console
    print(f"[upos_products] Số lượng sản phẩm khớp cuối cùng (đã lọc trùng): {len(matched)}")
    
    if not matched:
        # Tự động lấy 5 sản phẩm active để gợi ý nếu không tìm thấy
        suggestions = [item for item in raw_items if str(item.get("status", "1")) == "1"][:5]
        return _format_results([], suggestions=suggestions), suggestions

    for idx, item in enumerate(matched[:10]):
        name = item.get("product_name") or item.get("name")
        price = item.get("price") or item.get("sell_price")
        colors = item.get("color") or item.get("colors")
        sizes = item.get("size") or item.get("sizes")
        status = item.get("status")
        print(f"  {idx+1}. {name} | Giá: {price} | Màu: {colors} | Size: {sizes} | Status: {status}")

    return _format_results(matched, is_generic=(max_score == 0)), matched[:5]


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


def _format_results(items: list, suggestions: list = None, is_generic: bool = False) -> str:
    """Định dạng kết quả tìm kiếm thành string cho Miko đọc."""
    if not items:
        base_msg = "[KẾT QUẢ TÌM KIẾM: Không tìm thấy sản phẩm phù hợp với yêu cầu của khách.]"
        if suggestions:
            lines = [base_msg, "GỢI Ý CÁC SẢN PHẨM SẴN CÓ TẠI SHOP ĐỂ TƯ VẤN THÊM:"]
            for i, item in enumerate(suggestions, 1):
                name = item.get("name") or item.get("product_name", "Không rõ")
                price = _fmt_price(item.get("price") or item.get("sell_price"))
                lines.append(f"{i}. {name} — {price}")
            return "\n".join(lines)
        return base_msg

    # Nếu là tìm kiếm chung chung (không có từ khóa cụ thể), chỉ hiển thị list gợi ý
    if is_generic:
        lines = [
            f"[KẾT QUẢ TÌM KIẾM — {len(items)} sản phẩm (hiển thị tối đa 5)]",
            "DANH SÁCH SẢN PHẨM GỢI Ý ĐỂ BẠN GIỚI THIỆU CHO KHÁCH:"
        ]
        for i, item in enumerate(items[:5], 1):
            name = item.get("name") or item.get("product_name", "Không rõ")
            price = _fmt_price(item.get("price") or item.get("sell_price"))
            lines.append(f"{i}. {name} — {price}")
        if len(items) > 5:
            lines.append(f"...và {len(items) - 5} sản phẩm khác.")
        return "\n".join(lines)

    # Nếu có từ khóa cụ thể, luôn hiển thị CHI TIẾT cho sản phẩm Top 1 để Miko có dữ liệu tư vấn sâu
    top_item = items[0]
    name = top_item.get("name") or top_item.get("product_name", "Không rõ")
    price = _fmt_price(top_item.get("price") or top_item.get("sell_price"))
    sizes = top_item.get("sizes") or top_item.get("size", "Liên hệ để biết thêm")
    colors = top_item.get("colors") or top_item.get("color", "Liên hệ để biết thêm")
    sku = top_item.get("sku", "")
    
    if len(items) == 1:
        return (
            f"[KẾT QUẢ TÌM KIẾM — 1 sản phẩm]\n"
            f"1. {name} — {price}\n"
            f"   Size có sẵn: {sizes}\n"
            f"   Màu có sẵn: {colors}\n"
            f"   SKU: {sku}"
        )

    # Nếu có nhiều sản phẩm khớp, show chi tiết Top 1 và liệt kê ngắn gọn các món còn lại
    lines = [
        f"[KẾT QUẢ TÌM KIẾM — {len(items)} sản phẩm (hiển thị tối đa 5)]",
        "DANH SÁCH SẢN PHẨM PHÙ HỢP:",
        f"1. {name} — {price} (Sản phẩm phù hợp nhất)",
        f"   Size có sẵn: {sizes}",
        f"   Màu có sẵn: {colors}",
        f"   SKU: {sku}",
        "\nCÁC SẢN PHẨM KHÁC:"
    ]
    
    for i, item in enumerate(items[1:5], 2):
        other_name = item.get("name") or item.get("product_name", "Không rõ")
        other_price = _fmt_price(item.get("price") or item.get("sell_price"))
        lines.append(f"{i}. {other_name} — {other_price}")
        
    if len(items) > 5:
        lines.append(f"...và {len(items) - 5} sản phẩm khác.")
        
    return "\n".join(lines)


def _fmt_price(price) -> str:
    """Format giá tiền VNĐ."""
    try:
        return f"{int(price):,}đ".replace(",", ".")
    except (TypeError, ValueError):
        return "Liên hệ để biết giá"
