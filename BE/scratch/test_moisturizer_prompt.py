import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.append('.')
from models.ollama import call_ollama_api
from agents.miko import MIKO_SYSTEM_PROMPT

hint = " (BẮT BUỘC: Vì đây là mặt hàng cụ thể, bạn phải trả về DUY NHẤT một khối JSON 'search_product' để kiểm tra kho. Tuyệt đối không chat tự do ở lượt này)"

messages = [
    {"role": "system", "content": MIKO_SYSTEM_PROMPT},
    {"role": "user", "content": "shop mình có bán kem dưỡng ẩm không?" + hint}
]

print("=== LLM Response on Moisturizer ===")
print(call_ollama_api(messages))
