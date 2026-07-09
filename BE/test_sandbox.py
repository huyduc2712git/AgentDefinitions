import sys
import os

# Add BE folder to path so imports work
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from agents.miko import MIKO_SYSTEM_PROMPT, _call_llm
from tools.tool_executor import parse_intent

if __name__ == "__main__":
    test_cases = [
        "chốt Áo thun - M"
    ]
    
    for case in test_cases:
        print("="*60)
        print(f"User Message: {case}")
        messages = [
            {"role": "system", "content": MIKO_SYSTEM_PROMPT},
            {"role": "user", "content": case}
        ]
        
        reply = _call_llm(messages)
        intent = parse_intent(reply)
        print(f"Miko Reply: {reply}")
        print(f"Parsed Intent: {intent}")
