# app/schemas/mensagem.py - Schemas Pydantic para validação
# ==========================================================

from pydantic import BaseModel, Field


class MensagemInput(BaseModel):
    """Payload recebido do Lambda."""
    mensagem: str = Field(..., min_length=1, max_length=10000)


class MensagemResponse(BaseModel):
    """Resposta ao Lambda após criar o job."""
    id_job: str
    status: str = "pending"


class JobStatusResponse(BaseModel):
    """Resposta ao Lambda na consulta de status."""
    id_job: str
    status: str  # pending, processing, completed, failed
    mensagem: str | None = None
    resposta: str | None = None  # Preenchido quando status=completed

# ==========================================================
