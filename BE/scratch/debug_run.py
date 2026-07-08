import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.append('.')
import config
config.LLM_PROVIDER = "ollama"

from agents.miko import run_miko_turn
from session import store

# Clear session just in case
store.clear_session("debug_session_123")

# Modify miko.py run_miko_turn temporarily or print logs
# Let's inspect the messages and responses from Ollama by running it step-by-step
from agents.miko import _call_llm, MIKO_SYSTEM_PROMPT
from tools.tool_executor import parse_intent, execute

print("--- Step 1: User asks ---")
messages = [
    {"role": "system", "content": MIKO_SYSTEM_PROMPT},
    {"role": "user", "content": "shop có bán áo phao lông vũ không?"}
]
reply = _call_llm(messages)
print("LLM reply:", reply)
intent = parse_intent(reply)
print("Parsed intent:", intent)

if intent:
    tool_result = execute(intent)
    print("\n--- Step 2: Tool output ---")
    print("Tool result:", tool_result)
    
    messages.append({"role": "assistant", "content": reply})
    messages.append({
        "role": "user",
        "content": f"[Kết quả từ hệ thống]\n{tool_result}\n\nHãy dùng thông tin trên để trả lời khách."
    })
    
    reply2 = _call_llm(messages)
    print("\nLLM reply 2:", reply2)

