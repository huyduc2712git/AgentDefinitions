import os
import json
import requests

import config

MINIMAX_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

def call_minimax_api(messages: list, stream: bool = False, temperature: float = 0.7, max_tokens: int = 2048):
    """
    Hàm giao tiếp với API NVIDIA NIM.
    Hỗ trợ chuyển đổi động model và api key (Minimax / DeepSeek / Llama).
    """
    import os
    model_name = config.MINIMAX_MODEL
    
    # Chọn API Key tương ứng với model
    api_key = config.MINIMAX_API_KEY
    if "deepseek" in model_name.lower():
        api_key = os.environ.get("DEEPSEEKV4FLASH_API_KEY", config.MINIMAX_API_KEY).strip()
    elif "glm" in model_name.lower():
        api_key = os.environ.get("GLM52_API_KEY", config.MINIMAX_API_KEY).strip()
        
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "text/event-stream" if stream else "application/json",
    }
    payload = {
        "model": model_name,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": 0.95,
        "stream": stream,
    }

    try:
        response = requests.post(MINIMAX_URL, headers=headers, json=payload, stream=stream, timeout=60)
    except requests.exceptions.RequestException as e:
        raise Exception(f"Lỗi kết nối tới AI API (Nvidia): {e}")

    if not stream:
        if response.status_code != 200:
            raise Exception(f"Minimax API Error (Status {response.status_code}): {response.text}")
        data = response.json()
        return data["choices"][0]["message"]["content"]

    # Trường hợp stream
    full_text = ""
    for line in response.iter_lines():
        if line:
            decoded = line.decode("utf-8")
            if decoded.startswith("data: ") and decoded != "data: [DONE]":
                try:
                    chunk = json.loads(decoded[len("data: "):])
                    delta = chunk["choices"][0]["delta"].get("content", "")
                    full_text += delta
                except json.JSONDecodeError:
                    pass
    return full_text
