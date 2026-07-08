"""
services/upos_auth.py
Quản lý token UPOS: giữ token trong bộ nhớ, tự động login lại khi hết hạn.
"""
import requests
import config

# In-memory token cache (chia sẻ trong cùng 1 process)
_access_token: str = config.UPOS_ACCESS_TOKEN


def get_valid_token() -> str:
    """Trả về access token hiện tại (từ cache hoặc .env)."""
    global _access_token
    return _access_token


def login() -> str | None:
    """
    Đăng nhập bằng username/password, cập nhật token cache.
    Trả về access token mới nếu thành công, None nếu thất bại.
    """
    global _access_token
    try:
        resp = requests.post(
            config.UPOS_LOGIN_URL,
            json={"username": config.UPOS_USERNAME, "password": config.UPOS_PASSWORD, "shop_id": config.UPOS_SHOP_ID},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            # Xử lý cả hai cấu trúc phổ biến: data.access_token hoặc data.data.access_token
            token = (
                data.get("access_token")
                or data.get("data", {}).get("access_token")
            )
            if token:
                _access_token = token
                return token
        print(f"[upos_auth] Login failed: {resp.status_code} — {resp.text[:200]}")
    except Exception as e:
        print(f"[upos_auth] Login error: {e}")
    return None


def call_with_auth(method: str, url: str, **kwargs) -> requests.Response:
    """
    Gọi UPOS API với token hiện tại.
    Nếu nhận 401 (token hết hạn), tự động login lại và retry 1 lần.
    """
    global _access_token

    def _do_request(token: str) -> requests.Response:
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {token}"
        return requests.request(method, url, headers=headers, timeout=15, **kwargs)

    resp = _do_request(_access_token)

    # UPOS trả 200 nhưng body có auth_status: 401 khi token hết hạn.
    # Trong môi trường Dev, UPOS đôi khi crash 500 và trả về HTML error stacktrace chứa 'Expired token' hoặc 'JWT'
    is_expired = False
    if resp.status_code == 401:
        is_expired = True
    elif resp.status_code == 200:
        try:
            is_expired = (resp.json().get("auth_status") == 401)
        except Exception:
            pass
    elif resp.status_code == 500:
        err_text = resp.text.lower()
        if "expired" in err_text or "jwt" in err_text or "token" in err_text or "signature" in err_text:
            is_expired = True

    if is_expired:
        print("[upos_auth] Token expired or invalid (HTTP 500/401), re-logging in...")
        new_token = login()
        if new_token:
            resp = _do_request(new_token)

    return resp
