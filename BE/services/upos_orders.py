"""
services/upos_orders.py
Tạo đơn hàng trên UPOS API.
TODO: Xác nhận endpoint và payload thật với team UPOS.
"""
import re
import config
from services.upos_auth import call_with_auth


def validate_order(customer_name: str, phone: str, address: str, product_name: str,
                   quantity: int, **kwargs) -> str | None:
    """
    Validate thông tin đơn hàng.
    Trả về None nếu hợp lệ, trả về string mô tả lỗi nếu không hợp lệ.
    """
    errors = []

    if not customer_name or len(customer_name.strip()) < 2:
        errors.append("Họ tên không hợp lệ (cần ít nhất 2 ký tự).")

    phone_clean = re.sub(r"\D", "", phone or "")
    if not re.match(r"^(0[3-9]\d{8})$", phone_clean):
        errors.append("Số điện thoại không hợp lệ (cần 10 số, bắt đầu bằng 0[3-9]).")

    if not address or len(address.strip()) < 10:
        errors.append("Địa chỉ quá ngắn (cần mô tả rõ đường/số nhà/phường/quận).")

    if not product_name:
        errors.append("Thiếu tên sản phẩm.")

    try:
        if int(quantity) < 1:
            errors.append("Số lượng phải ít nhất là 1.")
    except (TypeError, ValueError):
        errors.append("Số lượng không hợp lệ.")

    return "; ".join(errors) if errors else None


def create_order(customer_name: str, phone: str, address: str, product_name: str,
                 quantity: int = 1, size: str = "", color: str = "") -> str:
    """
    Tạo đơn hàng trên UPOS.
    Trả về string thông báo kết quả để inject vào context của Miko.
    """
    # ── Validate trước ──
    err = validate_order(customer_name, phone, address, product_name, quantity,
                         size=size, color=color)
    if err:
        return f"[TẠO ĐƠN THẤT BẠI — Lý do: {err}]"

    phone_clean = re.sub(r"\D", "", phone)

    # ── Payload gửi lên UPOS ──
    # TODO: Điều chỉnh payload theo API thật của UPOS
    payload = {
        "customer_name": customer_name.strip(),
        "phone": phone_clean,
        "address": address.strip(),
        "products": [
            {
                "name": product_name,
                "quantity": int(quantity),
                "size": size or "",
                "color": color or "",
            }
        ],
        "payment_method": "COD",  # Mặc định COD, Miko sẽ hỏi thêm nếu cần
    }

    # ── Gọi API ──
    # TODO: Uncomment khi có endpoint thật. Hiện tại mock để demo.
    # resp = call_with_auth("POST", config.UPOS_CREATE_ORDER_URL, json=payload)
    # if resp.status_code == 200:
    #     data = resp.json()
    #     order_id = data.get("data", {}).get("order_id") or data.get("order_id", "N/A")
    #     return f"[TẠO ĐƠN THÀNH CÔNG — Mã đơn: {order_id}]"
    # else:
    #     return f"[TẠO ĐƠN THẤT BẠI — Lỗi hệ thống: {resp.status_code}]"

    # ── MOCK RESPONSE (xoá khi tích hợp thật) ──
    mock_order_id = f"ORD-MOCK-{phone_clean[-4:]}"
    summary = (
        f"[TẠO ĐƠN THÀNH CÔNG (MOCK)]\n"
        f"Mã đơn: {mock_order_id}\n"
        f"Khách: {customer_name} — SĐT: {phone_clean}\n"
        f"Địa chỉ: {address}\n"
        f"Sản phẩm: {product_name} x{quantity}"
        + (f" | Size: {size}" if size else "")
        + (f" | Màu: {color}" if color else "")
    )
    return summary
