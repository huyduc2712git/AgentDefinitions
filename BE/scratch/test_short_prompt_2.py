import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.append('.')
from models.ollama import call_ollama_api
from scratch.test_short_prompt import prompt_short

messages = [
    {"role": "system", "content": prompt_short},
    {"role": "user", "content": "shop có bán áo phao lông vũ không?"},
    {"role": "assistant", "content": '{\n  "action": "search_product",\n  "params": {\n    "query": "áo phao lông vũ"\n  }\n}'},
    {"role": "user", "content": "[Kết quả từ hệ thống]\n[KẾT QUẢ TÌM KIẾM: Không tìm thấy sản phẩm phù hợp với yêu cầu của khách.]\n\nHãy dùng thông tin trên để trả lời khách."}
]

print("--- Testing second turn (refusal) with short prompt ---")
print(call_ollama_api(messages))
