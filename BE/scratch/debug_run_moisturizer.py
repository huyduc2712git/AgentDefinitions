import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.append('.')
import config
config.LLM_PROVIDER = "ollama"

from agents.miko import run_miko_turn
from session import store

store.clear_session("debug_moisturizer_123")

print("--- Running run_miko_turn for moisturizer ---")
reply, products = run_miko_turn("shop mình có bán kem dưỡng ẩm không?", "debug_moisturizer_123")
print("\nFinal Reply:")
print(reply)
print("\nProducts list:")
print(products)
