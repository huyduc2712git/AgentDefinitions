"""
routes/chat.py
FastAPI router cho chat endpoint.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from agents.miko import run_miko_turn
from session import store

router = APIRouter()


class ChatRequest(BaseModel):
    session_id: str
    message: str


import json
import queue
import threading
from fastapi.responses import StreamingResponse

@router.post("/chat", summary="Gửi tin nhắn tới Miko (Stream Steps)")
def chat(req: ChatRequest):
    """
    Gửi tin nhắn và nhận phản hồi từ Miko AI dưới dạng stream các bước trạng thái thực tế.
    """
    q = queue.Queue()

    def on_status(status_type: str, message: str):
        q.put({"type": "status", "status": status_type, "message": message})

    def run_turn():
        try:
            reply, products = run_miko_turn(req.message, req.session_id, on_status=on_status)
            q.put({"type": "result", "reply": reply, "products": products})
        except Exception as e:
            print(f"[chat route] Error: {e}")
            reply = "Dạ hiện tại hệ thống AI đang quá tải hoặc phản hồi chậm. Anh/chị đợi một lát rồi thử lại giúp Miko nha! 🛠️"
            q.put({"type": "result", "reply": reply, "products": []})
        finally:
            q.put(None)  # Kết thúc stream

    # Chạy xử lý ở luồng phụ để luồng chính stream dữ liệu về
    t = threading.Thread(target=run_turn)
    t.start()

    def event_generator():
        while True:
            item = q.get()
            if item is None:
                break
            yield json.dumps(item, ensure_ascii=False) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")


@router.delete("/chat/{session_id}", summary="Reset cuộc hội thoại")
def clear_chat(session_id: str):
    """Xoá lịch sử hội thoại để bắt đầu lại."""
    store.clear_session(session_id)
    return {"message": f"Session '{session_id}' đã được reset."}


@router.get("/sessions", summary="Danh sách session đang active")
def list_sessions():
    """Debug endpoint: xem tất cả session đang có dữ liệu."""
    return {"sessions": store.list_sessions()}


@router.get("/chat/{session_id}/history", summary="Lấy lịch sử cuộc hội thoại")
def get_chat_history(session_id: str):
    """Debug endpoint: xem lịch sử của session."""
    return {"history": store.get_history(session_id)}
