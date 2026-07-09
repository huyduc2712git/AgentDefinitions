import os
from dotenv import load_dotenv

load_dotenv()

# ─── LLM Configuration ───
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "ollama").strip()  # "ollama" hoặc "nvidia"

MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY", "").strip()
MINIMAX_MODEL = os.environ.get("NVIDIA_MODEL", os.environ.get("MINIMAXM3_MODEL", "minimaxai/minimax-m3")).strip()
NVIDIA_BASE_URL = os.environ.get("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1").strip()

# ─── Ollama (Local LLM) ───
OLLAMA_API_URL = os.environ.get("OLLAMA_API_URL", "http://localhost:11434/api/chat")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:3b")
OLLAMA_TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT", 180))

# ─── UPOS API ───
UPOS_BASE_URL = os.environ.get("UPOS_BASE_URL", "https://api-dev.upos.vn/api/v3")

# Auth
UPOS_LOGIN_URL = f"{UPOS_BASE_URL}/auth/login"

# Products
UPOS_GET_ALL_PRODUCT_URL = f"{UPOS_BASE_URL}/product/list-all-product-details"
UPOS_SEARCH_PRODUCT_URL = f"{UPOS_BASE_URL}/product/list-all-product-details"  # Filter phía BE

# Orders — TODO: xác nhận endpoint thật với team UPOS
UPOS_CREATE_ORDER_URL = f"{UPOS_BASE_URL}/order/create"

# Credentials & tokens (dùng làm fallback khi token hết hạn)
UPOS_USERNAME = os.environ.get("UPOS_USERNAME", "admin")
UPOS_PASSWORD = os.environ.get("UPOS_PASSWORD", "jnt123!@#")
UPOS_SHOP_ID = os.environ.get("UPOS_SHOP_ID", "1")
UPOS_ACCESS_TOKEN = os.environ.get("UPOS_ACCESS_TOKEN", "")
UPOS_REFRESH_TOKEN = os.environ.get("UPOS_REFRESH_TOKEN", "")

# ─── Session ───
SESSION_MAX_HISTORY = 20  # Số lượt tối đa giữ trong history (sliding window)
TOOL_LOOP_MAX = 3          # Số lần tool-loop tối đa để tránh vòng lặp vô hạn
