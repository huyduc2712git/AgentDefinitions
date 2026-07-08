import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.append('.')
import config
config.LLM_PROVIDER = "ollama"

from agents.miko import run_miko_turn
from session import store

# Let's inspect step-by-step for hoodie
from agents.miko import _call_llm, MIKO_SYSTEM_PROMPT
from tools.tool_executor import parse_intent, execute

from agents.miko import run_miko_turn
from session import store

store.clear_session("debug_hoodie_final")

print("--- Running run_miko_turn for hoodie ---")
reply = run_miko_turn("shop mình có áo hoodie không?", "debug_hoodie_final")
print("\nFinal Reply:")
print(reply)

