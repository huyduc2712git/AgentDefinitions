import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.append('.')
from models.ollama import call_ollama_api
from agents.miko import MIKO_SYSTEM_PROMPT

messages = [
    {'role': 'system', 'content': MIKO_SYSTEM_PROMPT},
    {'role': 'user', 'content': 'shop có bán áo phao lông vũ 5 triệu không?'},
    {'role': 'assistant', 'content': '{"action": "search_product", "params": {"query": "áo phao lông vũ"}}'},
    {'role': 'system', 'content': '[HỆ THỐNG]: Kết quả tìm kiếm thực tế là: [KẾT QUẢ TÌM KIẾM: Không tìm thấy sản phẩm phù hợp với yêu cầu của khách.]. Hãy trả lời khách hàng là shop không có sản phẩm này. Tuyệt đối không được tự bịa ra thông tin sản phẩm.'}
]

print("=== SYSTEM message injection ===")
print(call_ollama_api(messages))

messages_user = [
    {'role': 'system', 'content': MIKO_SYSTEM_PROMPT},
    {'role': 'user', 'content': 'shop có bán áo phao lông vũ 5 triệu không?'},
    {'role': 'assistant', 'content': '{"action": "search_product", "params": {"query": "áo phao lông vũ"}}'},
    {'role': 'user', 'content': '[Kết quả từ hệ thống]\n[KẾT QUẢ TÌM KIẾM: Không tìm thấy sản phẩm phù hợp với yêu cầu của khách.]\n\nHãy dùng thông tin trên để trả lời khách.'}
]

print("\n=== USER message injection ===")
print(call_ollama_api(messages_user))
