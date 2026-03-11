# app/main.py - Aplicação FastAPI
# ===============================

from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(
    title="AI Agent API",
    description="API para receber mensagens do Lambda e gerenciar processamento via fila Redis",
)

app.include_router(router)


@app.get("/health")
def health():
    """Health check para monitoramento."""
    return {"status": "ok"}

# ===============================
