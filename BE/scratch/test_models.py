import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.append('BE')
import config
from models.minimax import call_minimax_api

models_to_test = [
    ("NVIDIA Cloud (Llama 3.1 8b)", "meta/llama-3.1-8b-instruct"),
    ("NVIDIA Cloud (DeepSeek v4 Flash)", "deepseek-ai/deepseek-v4-flash"),
    ("NVIDIA Cloud (GLM-5.2)", "z-ai/glm-5.2"),
    ("NVIDIA Cloud (MiniMax-M3)", "minimaxai/minimax-m3"),
]

messages = [{"role": "user", "content": "Xin chào, hãy nói 'hello' ngắn gọn"}]

for label, model_name in models_to_test:
    print(f"\n=== Testing model: {label} ===")
    print(f"Model ID: {model_name}")
    config.MINIMAX_MODEL = model_name
    
    try:
        reply = call_minimax_api(messages, stream=False)
        print(f"-> SUCCESS! Response: {reply.strip()}")
    except Exception as e:
        print(f"-> ERROR: {e}")
