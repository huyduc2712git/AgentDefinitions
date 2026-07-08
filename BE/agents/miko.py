"""
agents/miko.py
Miko — nhân viên tư vấn bán hàng UPOS.

Hàm chính: run_miko_turn(user_message, session_id)
  - Tải history từ session store
  - Gọi LLM → nếu ra JSON action, chạy tool-loop
  - Lưu history, trả về reply cuối cùng cho FE
"""
import re
import config
from models.ollama import call_ollama_api
from models.minimax import call_minimax_api
from tools.tool_executor import parse_intent, execute
from session import store

MIKO_SYSTEM_PROMPT = """
Bạn là Miko, nhân viên bán hàng của shop UPOS. Bạn chỉ được nói chuyện thân thiện (2-4 câu, có emoji) ở Chế độ 1 HOẶC trả về JSON hành động ở Chế độ 2.

[QUY TẮC BẮT BUỘC]
1. Ngay khi khách hỏi về sản phẩm hoặc hỏi shop có bán mặt hàng nào đó không (ví dụ: 'có kem dưỡng ẩm không', 'muốn mua áo thun'), bạn phải LẬP TỨC trả về JSON hành động 'search_product' để hệ thống tra cứu. TUYỆT ĐỐI không chat tự do hứa hẹn hay đoán trước là shop có hàng.
2. Bạn CHỈ được tư vấn sản phẩm dựa trên kết quả tìm kiếm thực tế do hệ thống trả về. Nếu hệ thống báo không tìm thấy, bạn phải lịch sự báo hết hàng hoặc shop chưa có. TUYỆT ĐỐI không tự bịa sản phẩm, mã số, hay giá cả.
3. Tuyệt đối KHÔNG hỏi khách về màu sắc/kích cỡ (size) đối với các mặt hàng không có các thuộc tính này (ví dụ: mỹ phẩm, kem dưỡng ẩm, thực phẩm...). Chỉ hỏi size/màu khi khách mua quần áo, giày dép.

[ĐỊNH DẠNG ĐẦU RA (OUTPUT FORMAT)]
- Chế độ 1 (Nói chuyện tự do): Trả lời bằng văn bản tự nhiên theo Persona của Miko (dạ, ạ, vâng, nha...).
- Chế độ 2 (Gọi hành động): TRẢ VỀ DUY NHẤT MỘT KHỐI JSON sau:

{
  "action": "search_product",
  "params": {
    "query": "tên sản phẩm",
    "color": "màu sắc (chỉ điền nếu là quần áo và khách có nhắc tới)",
    "size": "kích thước/dung tích (chỉ điền nếu có)"
  }
}
Hoặc khi khách chốt mua và đã cung cấp đủ (họ tên, SĐT, địa chỉ giao hàng, sản phẩm, số lượng, size/màu):
{
  "action": "create_order",
  "params": {
    "customer_name": "...",
    "phone": "...",
    "address": "...",
    "product_name": "...",
    "quantity": 1,
    "size": "...",
    "color": "..."
  }
}
"""


def _call_llm(messages: list, stream: bool = False) -> str:
    """Gọi LLM dựa trên cấu hình LLM_PROVIDER."""
    if config.LLM_PROVIDER == "nvidia":
        return call_minimax_api(messages=messages, stream=stream, temperature=0.7)
    else:
        return call_ollama_api(messages=messages, stream=stream, temperature=0.7)


def get_hint(message: str) -> str:
    msg_lower = message.lower().strip()
    greetings = ["chào", "hello", "hi", "alo", "helo", "heyy"]
    checkout_keywords = ["địa chỉ", "sđt", "số điện thoại", "giao tới", "ship", "chốt mua", "đặt mua", "chốt đơn"]
    has_phone = bool(re.search(r"\b0[3-9]\d{8}\b", msg_lower))

    # 1. Chào hỏi ngắn
    if len(msg_lower) < 15 and any(g in msg_lower for g in greetings):
        return " (Hãy chào khách thân thiện Chế độ 1)"

    # 2. Khách chốt đơn và cung cấp thông tin liên hệ (Có SĐT hoặc địa chỉ) -> Gọi tool tạo đơn
    if has_phone or any(kw in msg_lower for kw in checkout_keywords):
        if has_phone or "địa chỉ" in msg_lower or "sđt" in msg_lower or "giao" in msg_lower or "ship" in msg_lower:
            return " (BẮT BUỘC: Khách hàng đang chốt đơn và cung cấp thông tin giao hàng, hãy lập tức trả về JSON 'create_order' với các thông tin đã có. Tuyệt đối không gọi search_product ở lượt này)"

    # 3. Khách nói chốt/mua sản phẩm cụ thể nhưng chưa đưa SĐT/địa chỉ -> Chat xin thông tin giao hàng
    buy_intent_keywords = ["chốt", "mua", "lấy", "đặt"]
    if any(kw in msg_lower for kw in buy_intent_keywords):
        return " (Hãy trò chuyện tự do ở Chế độ 1 để cám ơn khách và lịch sự xin thông tin giao hàng bao gồm họ tên, SĐT, địa chỉ để lên đơn. Tuyệt đối không gọi search_product ở lượt này)"

    # 4. Tìm kiếm sản phẩm thông thường
    return " (BẮT BUỘC: Vì đây là câu hỏi tìm kiếm mặt hàng/sản phẩm, bạn phải trả về DUY NHẤT một khối JSON 'search_product' để tra cứu kho. Tuyệt đối không chat tự do ở lượt này)"


def run_miko_turn(user_message: str, session_id: str, stream: bool = False, on_status = None) -> tuple[str, list]:
    """
    Xử lý một lượt hội thoại của Miko.
    - Load history từ session store
    - Gọi LLM, phát hiện JSON action nếu có
    - Chạy tool-loop (tối đa TOOL_LOOP_MAX lần) để resolve action
    - Lưu history, trả về reply cho FE
    """
    # ── Build messages ──
    history = store.get_history(session_id)
    messages = [{"role": "system", "content": MIKO_SYSTEM_PROMPT}]
    messages.extend(history)
    
    # Thêm hint helper động cho Llama local dễ chọn đúng chế độ JSON / Chat tự do
    hint = get_hint(user_message)
    messages.append({"role": "user", "content": user_message + hint})

    final_reply = ""
    tool_calls = 0
    found_products = []

    if on_status:
        on_status("thinking", "Miko đang suy nghĩ...")

    while tool_calls <= config.TOOL_LOOP_MAX:
        reply = _call_llm(messages, stream=stream)
        intent = parse_intent(reply)

        if intent is None:
            # Miko trả lời tự do — đây là reply cuối
            final_reply = re.sub(r'^(?:Chế độ\s*\d+\s*(?:\([^)]+\))?\s*:\s*)', '', reply, flags=re.IGNORECASE).strip()
            break

        # Miko ra JSON → chạy tool
        tool_calls += 1
        if on_status:
            on_status("searching", "Đang kết nối API và kiểm tra kho hàng...")
        tool_result, current_products = execute(intent)
        if current_products:
            found_products = current_products
        print(f"[miko] Tool call #{tool_calls}: {intent.get('action')} → {tool_result[:100]}...")

        if on_status:
            on_status("answering", "Miko đang đối chiếu sản phẩm và soạn câu trả lời...")

        # Inject tool result vào messages như một system message
        messages.append({"role": "assistant", "content": reply})
        messages.append({
            "role": "user",
            "content": f"[Kết quả từ hệ thống]\n{tool_result}\n\nHãy dùng thông tin trên để trả lời khách."
        })

        if tool_calls > config.TOOL_LOOP_MAX:
            final_reply = "Dạ hệ thống đang xử lý, anh/chị chờ mình một chút nhé ạ! 🙏"
            break

    # ── Lưu history (chỉ lưu lượt user gốc + reply cuối) ──
    store.append_turn(session_id, user_message, final_reply)

    return final_reply, found_products


# ── Backward compat cho main.py cũ ──
def call_miko(user_message: str, history: list = None, stream: bool = False) -> str:
    """Legacy helper — dùng session_id tạm thời."""
    session_id = "legacy_main"
    if history:
        # Nạp history từ caller (không dùng session store)
        messages = [{"role": "system", "content": MIKO_SYSTEM_PROMPT}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})
        return _call_llm(messages, stream=stream)
    reply, _ = run_miko_turn(user_message, session_id, stream=stream)
    return reply
