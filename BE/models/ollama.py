import json
import requests
import config


def call_ollama_api(
    messages: list,
    stream: bool = False,
    temperature: float = 0.7,
) -> str:
    """
    Gọi Ollama chạy ở localhost (dựa trên config.OLLAMA_API_URL).
    """
    payload = {
        "model": config.OLLAMA_MODEL,
        "messages": messages,
        "stream": stream,
        "options": {
            "temperature": temperature,
        }
    }

    try:
        response = requests.post(
            config.OLLAMA_API_URL,
            json=payload,
            stream=stream,
            timeout=config.OLLAMA_TIMEOUT
        )
    except requests.exceptions.RequestException as e:
        raise Exception(f"Lỗi kết nối tới Ollama: {e}")

    if not stream:
        if response.status_code != 200:
            raise Exception(f"Ollama API Error (Status {response.status_code}): {response.text}")
        data = response.json()
        return data.get("message", {}).get("content", "")

    # Trường hợp stream
    full_text = ""
    for line in response.iter_lines():
        if line:
            decoded = line.decode("utf-8")
            try:
                chunk = json.loads(decoded)
                delta = chunk.get("message", {}).get("content", "")
                full_text += delta
                print(delta, end="", flush=True)
                if chunk.get("done"):
                    break
            except json.JSONDecodeError:
                pass
    return full_text
