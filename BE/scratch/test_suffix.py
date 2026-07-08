import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.append('.')
from models.ollama import call_ollama_api
from agents.miko import MIKO_SYSTEM_PROMPT

# Suffix to guide Llama 3.2 3B on its decision
suffix = " (Nếu khách hỏi về sản phẩm, hãy trả về DUY NHẤT một khối JSON 'search_product'. Ngược lại trả lời tự do Chế độ 1)"

messages = [
    {"role": "system", "content": MIKO_SYSTEM_PROMPT},
    {"role": "user", "content": "shop mình có áo hoodie không?" + suffix}
]

print("--- Testing with user message suffix ---")
print(call_ollama_api(messages))
