import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.append('.')
from models.ollama import call_ollama_api
from agents.miko import MIKO_SYSTEM_PROMPT

hint = " (Nếu câu hỏi đề cập hoặc hỏi mua bất kỳ mặt hàng/sản phẩm nào, bạn BẮT BUỘC phải trả về duy nhất JSON 'search_product' để kiểm tra kho. Ngược lại, nếu chỉ là chào hỏi hoặc hỏi thăm thông thường, hãy trả lời tự do Chế độ 1)"

messages_greeting = [
    {"role": "system", "content": MIKO_SYSTEM_PROMPT},
    {"role": "user", "content": "chào em nha" + hint}
]

messages_search = [
    {"role": "system", "content": MIKO_SYSTEM_PROMPT},
    {"role": "user", "content": "shop mình có bán kem dưỡng ẩm không?" + hint}
]

print("=== Greeting Response ===")
print(call_ollama_api(messages_greeting))

print("\n=== Search Response ===")
print(call_ollama_api(messages_search))
