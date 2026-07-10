"""
tools/tool_executor.py
Parse JSON intent từ Miko và dispatch tới service tương ứng.
"""
import json
import re


def parse_intent(llm_response: str) -> dict | None:
    """
    Kiểm tra xem response của LLM có chứa JSON action hay không.
    Xử lý 3 trường hợp:
    1. JSON thuần (toàn bộ response là JSON)
    2. JSON trong code-fence ```json ... ```
    3. JSON lẫn trong text tự do (LLM không tuân thủ format)
    Trả về dict {action, params} nếu hợp lệ, None nếu là text thuần.
    """
    text = llm_response.strip()

    # ── Trường hợp 1: JSON thuần ──
    try:
        data = json.loads(text)
        if isinstance(data, dict) and "action" in data:
            return data
    except (json.JSONDecodeError, ValueError):
        pass

    # ── Trường hợp 2: JSON trong code-fence ──
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence_match:
        try:
            data = json.loads(fence_match.group(1))
            if isinstance(data, dict) and "action" in data:
                return data
        except (json.JSONDecodeError, ValueError):
            pass

    # ── Trường hợp 3: JSON lẫn trong text (LLM vi phạm format) ──
    # Dùng bracket-counting để tìm JSON object đầu tiên trong text
    extracted = _extract_first_json_object(text)
    if extracted:
        try:
            data = json.loads(extracted)
            if isinstance(data, dict) and "action" in data:
                return data
        except (json.JSONDecodeError, ValueError):
            pass

    return None


def _extract_first_json_object(text: str) -> str | None:
    """
    Tìm JSON object đầu tiên trong text bằng cách đếm ngoặc nhọn.
    Xử lý đúng nested objects (vd: {"action": "...", "params": {...}}).
    """
    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escape_next = False

    for i, ch in enumerate(text[start:], start=start):
        if escape_next:
            escape_next = False
            continue
        if ch == "\\" and in_string:
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return None


def execute(intent: dict) -> tuple[str, list]:
    """
    Chạy tool tương ứng với intent, trả về string kết quả để inject vào history và danh sách dữ liệu (nếu có).
    """
    action = intent.get("action", "")
    params = intent.get("params", {})

    if action == "search_product":
        from services.upos_products import search_product
        res_str, items = search_product(
            query=params.get("query", ""),
            size=params.get("size", ""),
            color=params.get("color", ""),
        )
        return res_str, items

    elif action == "create_order":
        from services.upos_orders import create_order
        phone_val = params.get("phone") or params.get("customer_phone", "") or params.get("sdt", "")
        address_val = params.get("address") or params.get("customer_address", "") or params.get("dia_chi", "")
        prod_name_val = params.get("product_name") or params.get("name") or params.get("product", "") or params.get("ten_san_pham", "")
        res_str = create_order(
            customer_name=params.get("customer_name", "") or params.get("name_customer", "") or params.get("ten_khach_hang", ""),
            phone=phone_val,
            address=address_val,
            product_name=prod_name_val,
            quantity=params.get("quantity", 1) or params.get("so_luong", 1),
            size=params.get("size", "") or params.get("kich_thuoc", ""),
            color=params.get("color", "") or params.get("mau_sac", ""),
        )
        return res_str, []

    else:
        return f"[Hệ thống: Action '{action}' không được hỗ trợ.]", []
