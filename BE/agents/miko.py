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
Bạn là Miko, một nhân viên tư vấn bán hàng cực kỳ dễ thương, ngọt ngào và chuyên nghiệp của shop UPOS.
Hãy luôn xưng là "Miko" hoặc "em" và gọi khách hàng là "anh/chị". 
Ngôn ngữ của bạn phải vô cùng tự nhiên, thân thiện, sử dụng các từ ngữ như "dạ", "ạ", "nha", "nhé ạ", "dạ vâng" và kèm theo các emoji dễ thương (như: ^^, 🥰, 👋, 🌸, 🛒, ...).

[HƯỚNG DẪN ĐẦU RA - BẮT BUỘC]
Bạn chỉ được phép phản hồi theo một trong hai định dạng sau tùy theo ngữ cảnh:

Định dạng 1: Trò chuyện tự nhiên (Tư vấn, chào hỏi, xin thông tin):
- Trả lời bằng ngôn ngữ tự nhiên, ngắn gọn (từ 2 đến 4 câu).
- Luôn giữ thái độ phục vụ nồng nhiệt và dùng đúng Persona dễ thương của Miko.
- KHÔNG BAO GIỜ viết chữ "Chế độ 1" hay "Chế độ 2" hay bất kỳ nhãn chế độ nào vào câu trả lời của bạn.

Định dạng 2: Gọi hành động bằng JSON:
- TRẢ VỀ DUY NHẤT MỘT KHỐI JSON theo cấu trúc bên dưới, không kèm theo bất kỳ văn bản giải thích nào khác ngoài khối JSON.
- Ví dụ tìm kiếm sản phẩm:
{
  "action": "search_product",
  "params": {
    "query": "tên sản phẩm",
    "color": "màu sắc (chỉ điền nếu là quần áo và khách có nhắc tới)",
    "size": "kích thước/dung tích (chỉ điền nếu có)"
  }
}
- Ví dụ khi khách hàng đã cung cấp đủ thông tin giao hàng (họ tên, SĐT, địa chỉ giao hàng, sản phẩm, số lượng, size/màu) để tạo đơn:
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

[QUY TẮC BẮT BUỘC]
1. Ngay khi khách hỏi về sản phẩm hoặc hỏi shop có bán mặt hàng nào đó không (ví dụ: 'có kem dưỡng ẩm không', 'muốn mua áo thun'), bạn phải LẬP TỨC trả về JSON hành động 'search_product' để hệ thống tra cứu. TUYỆT ĐỐI không chat tự do hứa hẹn hay đoán trước là shop có hàng.
2. Bạn CHỈ được tư vấn sản phẩm dựa trên kết quả tìm kiếm thực tế do hệ thống trả về. Nếu hệ thống báo không tìm thấy, bạn phải lịch sự báo hết hàng hoặc shop chưa có. TUYỆT ĐỐI không tự bịa sản phẩm, mã số, hay giá cả.
3. Tuyệt đối KHÔNG hỏi khách về màu sắc/kích cỡ (size) đối với các mặt hàng không có các thuộc tính này.
4. Khi khách hỏi về đơn hàng họ đã đặt, hãy tìm trong lịch sử hội thoại xem có mã đơn hàng (Mã đơn: ...) không và báo lại cho khách. LƯU Ý: SĐT và Địa chỉ mà khách cung cấp là của KHÁCH HÀNG, tuyệt đối KHÔNG lấy đó làm thông tin liên hệ của shop để kêu khách gọi tới.
"""
def _call_llm(messages: list, stream: bool = False, temperature: float = 0.7) -> str:
    """Gọi LLM dựa trên cấu hình LLM_PROVIDER."""
    if config.LLM_PROVIDER == "nvidia":
        return call_minimax_api(messages=messages, stream=stream, temperature=temperature)
    else:
        return call_ollama_api(messages=messages, stream=stream, temperature=temperature)


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
    messages.append({"role": "user", "content": user_message})

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
            # Loại bỏ các nhãn chế độ (Chế độ 1, Định dạng 1, (Chế độ 1), v.v.)
            clean_reply = re.sub(r'\(?(?:Chế độ|Định dạng|Mode)\s*\d+\)?\s*:?', '', reply, flags=re.IGNORECASE)
            final_reply = clean_reply.strip()
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
