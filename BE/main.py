"""
main.py — FastAPI app entry point
Chạy: uvicorn main:app --reload --port 8000
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.chat import router as chat_router

app = FastAPI(
    title="Miko AI Agent API",
    description="Backend AI Agent tư vấn bán hàng UPOS — Powered by Minimax",
    version="1.0.0",
)

# CORS — cho phép FE/Zalo OA gọi vào
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Giới hạn domain thật khi deploy production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, tags=["Chat"])


from pydantic import BaseModel

class ConfigUpdate(BaseModel):
    llm_provider: str
    nvidia_model: str | None = None

@app.get("/config", tags=["Config"])
def get_backend_config():
    import config
    return {
        "llm_provider": config.LLM_PROVIDER,
        "model": config.MINIMAX_MODEL
    }

@app.post("/config", tags=["Config"])
def update_backend_config(cfg: ConfigUpdate):
    import config
    if cfg.llm_provider in ("ollama", "nvidia"):
        config.LLM_PROVIDER = cfg.llm_provider
        if cfg.nvidia_model:
            config.MINIMAX_MODEL = cfg.nvidia_model
        return {
            "status": "success", 
            "llm_provider": config.LLM_PROVIDER, 
            "model": config.MINIMAX_MODEL
        }
    return {"status": "error", "message": "Invalid provider"}

@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "agent": "Miko", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}