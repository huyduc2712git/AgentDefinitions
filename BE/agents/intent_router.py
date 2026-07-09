"""
agents/intent_router.py
Hybrid 2.5 lớp Intent Router cho Miko:
  Layer 1   — Regex pre-filter (0ms, miễn phí)  : catch 60-70% câu rõ ràng
  Layer 2   — LLM classify (1 call rẻ, ~150 token) : catch câu mơ hồ
  Layer 2.5 — Guard parsing + auto-router         : trả (intent, action_type)

Entry point: classify_and_route(user_msg) -> (intent, action_type)
  - intent:      "GREETING" | "CHITCHAT" | "SEARCH_PRODUCT" | "CREATE_ORDER" | None
  - action_type: "auto_search" | "auto_order" | "free_chat" | None

Khi intent/action là None → caller (miko.py) sẽ fallback về logic cũ.
"""
import re
import config
from agents.prompts import (
    INTENT_CLASSIFY_PROMPT,
    VALID_INTENTS,
    INTENT_TO_ACTION,
)


# ────────────────────────────────────────────────────────────
# LAYER 1: REGEX RULES
# Thứ tự quan trọng: rule nào match trước sẽ thắng.
# SĐT ưu tiên cao nhất vì nó là dấu hiệu rất chắc chắn của CREATE_ORDER.
# ────────────────────────────────────────────────────────────
REGEX_RULES = [
    # SĐT Việt Nam 10 số, bắt đầu 03-09 → rất chắc chắn là CREATE_ORDER context
    (r"0[3-9]\d{8}", "CREATE_ORDER"),
    # Câu chào thuần (chỉ 1-3 từ, không kèm câu hỏi) → GREETING
    (r"^(chào|hi|hello|hey|xin chào)\s*(shop|miko|bạn|em)?\.?$", "GREETING"),
    # Keyword hỏi thông tin shop → CHITCHAT
    (r"\b(mở cửa|đóng cửa|địa chỉ|ở đâu|freeship|free ship|ship|giờ|khuyến mãi|giảm giá|sale|liên hệ)\b", "CHITCHAT"),
]


def classify_intent_regex(text: str) -> str | None:
    """
    Layer 1: duyệt REGEX_RULES, trả intent đầu tiên match, None nếu không match.

    Ví dụ:
        classify_intent_regex("0912345678") -> "CREATE_ORDER"
        classify_intent_regex("chào")        -> "GREETING"
        classify_intent_regex("có áo hoodie không") -> None
    """
    if not text:
        return None
    text_lower = text.lower().strip()
    for pattern, intent in REGEX_RULES:
        if re.search(pattern, text_lower):
            return intent
    return None


# ────────────────────────────────────────────────────────────
# LAYER 2: LLM CLASSIFY
# Gọi LLM 1 lần với prompt ngắn + few-shot. Guard parsing kỹ.
# ────────────────────────────────────────────────────────────
def _call_llm(messages: list, stream: bool = False, temperature: float = 0.0, max_tokens: int = 8) -> str:
    """
    Gọi LLM dựa trên config.LLM_PROVIDER. Copy logic từ miko.py để tránh circular import.
    """
    if config.LLM_PROVIDER == "nvidia":
        from models.minimax import call_minimax_api
        return call_minimax_api(messages=messages, stream=stream, temperature=temperature, max_tokens=max_tokens)
    else:
        from models.ollama import call_ollama_api
        return call_ollama_api(messages=messages, stream=stream, temperature=temperature)


def classify_intent_llm(text: str, history: list = None) -> str | None:
    """
    Layer 2: gọi LLM classify intent.
    """
    if not text or not text.strip():
        return None

    history_context = "(Không có lịch sử)"
    if history:
        recent = history[-2:]
        lines = []
        for msg in recent:
            role = "Khách" if msg.get("role") == "user" else "Miko"
            lines.append(f"{role}: {msg.get('content')}")
        history_context = "\n".join(lines)

    prompt = INTENT_CLASSIFY_PROMPT.format(history_context=history_context, user_msg=text.strip())
    messages = [
        {"role": "system", "content": "Bạn là bộ phân loại intent. Chỉ trả đúng 1 từ trong 4 loại: GREETING, CHITCHAT, SEARCH_PRODUCT, CREATE_ORDER."},
        {"role": "user", "content": prompt},
    ]

    try:
        raw = _call_llm(messages, stream=False, temperature=0.0, max_tokens=8)
    except Exception as e:
        print(f"[intent_router] LLM classify fail: {e}")
        return None

    raw_clean = raw.strip().upper()
    for intent in VALID_INTENTS:
        if re.search(rf"\b{re.escape(intent)}\b", raw_clean):
            return intent

    print(f"[intent_router] LLM output không khớp intent hợp lệ: {raw!r}")
    return None


# ────────────────────────────────────────────────────────────
# LAYER 2.5: ROUTER
# Map intent → action type (auto_search | auto_order | free_chat)
# ────────────────────────────────────────────────────────────
def route(intent: str | None) -> str | None:
    """
    Map intent → action type. Trả None nếu intent không hợp lệ.
    """
    if intent is None:
        return None
    return INTENT_TO_ACTION.get(intent)


# ────────────────────────────────────────────────────────────
# ENTRY POINT
# ────────────────────────────────────────────────────────────
def classify_and_route(text: str, history: list = None) -> tuple[str | None, str | None]:
    """
    Entry point: phân loại intent + quyết định action.
    """
    # ── Layer 1: Regex ──
    intent = classify_intent_regex(text)
    if intent:
        print(f"[intent_router] Layer 1 (regex): {intent}")
        return intent, route(intent)

    # ── Layer 2: LLM classify ──
    intent = classify_intent_llm(text, history)
    if intent:
        print(f"[intent_router] Layer 2 (LLM): {intent}")
        return intent, route(intent)

    # ── Fail → caller sẽ fallback ──
    print(f"[intent_router] Cả 2 layer đều fail, fallback.")
    return None, None
