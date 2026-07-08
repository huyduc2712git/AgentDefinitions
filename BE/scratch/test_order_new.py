import sys
import re
sys.stdout.reconfigure(encoding='utf-8')
sys.path.append('.')
from models.ollama import call_ollama_api
from agents.miko import MIKO_SYSTEM_PROMPT

def get_hint(message: str) -> str:
    msg_lower = message.lower().strip()
    greetings = ["chào", "hello", "hi", "alo", "helo", "heyy"]
    checkout_keywords = ["địa chỉ", "sđt", "số điện thoại", "giao tới", "ship", "chốt mua", "đặt mua", "chốt đơn"]
    has_phone = bool(re.search(r"\b0[3-9]\d{8}\b", msg_lower))
    
    if len(msg_lower) < 15 and any(g in msg_lower for g in greetings):
        return " (Hãy chào khách thân thiện Chế độ 1)"
        
    if has_phone or any(kw in msg_lower for kw in checkout_keywords):
        return " (BẮT BUỘC: Khách hàng đang chốt đơn và cung cấp thông tin giao hàng, hãy lập tức trả về JSON 'create_order' với các thông tin đã có. Tuyệt đối không gọi search_product ở lượt này)"
        
    return " (BẮT BUỘC: Vì đây là câu hỏi tìm kiếm mặt hàng/sản phẩm, bạn phải trả về DUY NHẤT một khối JSON 'search_product' để tra cứu kho. Tuyệt đối không chat tự do ở lượt này)"

user_msg = "mình chốt áo thun này nhé, thông tin mình là: Nguyễn Văn A, SĐT: 0987654321, địa chỉ: 123 Nguyễn Trãi, Phường 2, Quận 5, TP.HCM, size L, màu trắng"

messages = [
    {"role": "system", "content": MIKO_SYSTEM_PROMPT},
    {"role": "user", "content": user_msg + get_hint(user_msg)}
]

print("=== LLM Response ===")
print(call_ollama_api(messages))
