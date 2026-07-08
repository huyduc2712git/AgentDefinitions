import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.append('.')
import config
config.LLM_PROVIDER = "ollama"

from agents.miko import run_miko_turn
from session import store

store.clear_session("debug_order_123")

# Bước 1: Khách hỏi tìm áo thun
print("=== BƯỚC 1: Khách hỏi tìm áo thun ===")
reply, products = run_miko_turn("shop mình có áo thun không?", "debug_order_123")
print("Miko:", reply)
print("Products returned to UI:", len(products))

# Bước 2: Khách chốt đơn và cung cấp thông tin
print("\n=== BƯỚC 2: Khách cung cấp thông tin chốt đơn ===")
user_msg = "mình chốt áo thun này nhé, thông tin mình là: Nguyễn Văn A, SĐT: 0987654321, địa chỉ: 123 Nguyễn Trãi, Phường 2, Quận 5, TP.HCM, size L, màu trắng"
reply, products = run_miko_turn(user_msg, "debug_order_123")
print("Miko:", reply)
