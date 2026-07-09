"""
session/store.py
In-memory session store: lưu lịch sử hội thoại theo session_id.
Interface đơn giản — có thể swap sang Redis sau mà không cần sửa code tầng trên.
"""
import config
from collections import defaultdict
from threading import Lock

_store: dict[str, list] = defaultdict(list)
_last_products: dict[str, list] = defaultdict(list)
_current_product: dict[str, dict] = defaultdict(dict)
_lock = Lock()


def get_history(session_id: str) -> list:
    """Trả về copy của history cho session."""
    with _lock:
        return list(_store[session_id])


def save_last_products(session_id: str, products: list) -> None:
    """Lưu danh sách sản phẩm tìm được gần nhất của session."""
    with _lock:
        _last_products[session_id] = list(products)


def get_last_products(session_id: str) -> list:
    """Lấy danh sách sản phẩm tìm được gần nhất của session."""
    with _lock:
        return list(_last_products.get(session_id, []))


def save_current_product(session_id: str, product: dict) -> None:
    """Lưu sản phẩm đang được chọn/chốt của session."""
    with _lock:
        _current_product[session_id] = dict(product)


def get_current_product(session_id: str) -> dict:
    """Lấy sản phẩm đang được chọn/chốt của session."""
    with _lock:
        return dict(_current_product.get(session_id, {}))


def save_history(session_id: str, messages: list) -> None:
    """
    Lưu lại toàn bộ history (sau khi đã append message mới).
    Áp dụng sliding window: chỉ giữ lại SESSION_MAX_HISTORY lượt gần nhất
    (1 lượt = 1 user message + 1 assistant message = 2 items).
    """
    with _lock:
        # Giữ system message (index 0) + N lượt cuối
        if len(messages) > config.SESSION_MAX_HISTORY + 1:
            system_msg = messages[0] if messages[0]["role"] == "system" else None
            tail = messages[-(config.SESSION_MAX_HISTORY):]
            _store[session_id] = ([system_msg] if system_msg else []) + tail
        else:
            _store[session_id] = list(messages)


def append_turn(session_id: str, user_msg: str, assistant_reply: str) -> list:
    """
    Thêm 1 lượt hội thoại (user + assistant) vào history.
    Trả về history mới sau khi đã append.
    """
    with _lock:
        history = _store[session_id]
        history.append({"role": "user", "content": user_msg})
        history.append({"role": "assistant", "content": assistant_reply})

        # Sliding window (không tính system message)
        non_system = [m for m in history if m["role"] != "system"]
        system_msgs = [m for m in history if m["role"] == "system"]
        if len(non_system) > config.SESSION_MAX_HISTORY:
            non_system = non_system[-config.SESSION_MAX_HISTORY:]
        _store[session_id] = system_msgs + non_system
        return list(_store[session_id])


def clear_session(session_id: str) -> None:
    """Xoá toàn bộ history của một session."""
    with _lock:
        _store.pop(session_id, None)
        _last_products.pop(session_id, None)
        _current_product.pop(session_id, None)


def list_sessions() -> list[str]:
    """Trả về danh sách tất cả session đang active."""
    with _lock:
        return list(_store.keys())
