import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.append('.')
from models.ollama import call_ollama_api
from agents.miko import MIKO_SYSTEM_PROMPT

def get_hint(message: str) -> str:
    msg_lower = message.lower().strip()
    greetings = ["chào", "hello", "hi", "alo", "helo", "heyy"]
    if len(msg_lower) < 15 and any(g in msg_lower for g in greetings):
        return " (Hãy chào khách thân thiện Chế độ 1)"
    return " (BẮT BUỘC: Vì đây là câu hỏi tìm kiếm mặt hàng/sản phẩm, bạn phải trả về DUY NHẤT một khối JSON 'search_product' để tra cứu kho. Tuyệt đối không chat tự do ở lượt này)"

# Greeting
user_msg_1 = "chào em nha"
messages_1 = [
    {"role": "system", "content": MIKO_SYSTEM_PROMPT},
    {"role": "user", "content": user_msg_1 + get_hint(user_msg_1)}
]

# Product query
user_msg_2 = "shop mình có bán kem dưỡng ẩm không?"
messages_2 = [
    {"role": "system", "content": MIKO_SYSTEM_PROMPT},
    {"role": "user", "content": user_msg_2 + get_hint(user_msg_2)}
]

print("=== Greeting Response ===")
print(call_ollama_api(messages_1))

print("\n=== Search Response ===")
print(call_ollama_api(messages_2))
