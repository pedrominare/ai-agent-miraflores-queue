# app/api/routes.py - Endpoints da API
# ====================================

from fastapi import APIRouter, HTTPException, Header, Depends

from app.schemas.mensagem import MensagemInput, MensagemResponse, JobStatusResponse
from app.db.models import create_job, get_job
from app.queue.producer import enqueue
from app.config import API_KEY

router = APIRouter(prefix="/api", tags=["api"])


def verify_api_key(x_api_key: str | None = Header(None)):
    """Valida API key se configurada."""
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="API key inválida")
    return True


@router.post("/mensagens", response_model=MensagemResponse)
def receber_mensagem(
    payload: MensagemInput,
    _: bool = Depends(verify_api_key),
):
    """
    Recebe mensagem do Lambda, cria job, enfileira e retorna id_job.
    """
    id_job = create_job(payload.mensagem)
    enqueue(id_job)
    return MensagemResponse(id_job=id_job, status="pending")


@router.get("/jobs/{id_job}", response_model=JobStatusResponse)
def consultar_status(
    id_job: str,
    _: bool = Depends(verify_api_key),
):
    """
    Lambda consulta status do job e resposta (quando completed).
    """
    job = get_job(id_job)
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    return JobStatusResponse(
        id_job=job["id_job"],
        status=job["status"],
        mensagem=job["mensagem"],
        resposta=job["resposta"],
    )

# ====================================
