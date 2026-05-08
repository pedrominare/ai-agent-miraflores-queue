# app/processors/cock_ascii.py - Processamento da rota /cock-ascii
# ========================================================================
# Processor separado para a rota /cock-ascii. Mantém a lógica simples
# e isolada, podendo evoluir de forma independente do processar_mensagem.
# ========================================================================

import time
import logging
from app.db.models import get_job
from app.processors import pica

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def processar_example(id_job: str) -> str:
    """
    Processa o job criado pela rota /example.
    Por enquanto apenas lê a mensagem e devolve uma resposta simples.
    """
    job = get_job(id_job)
    if not job:
        logger.warning(f"Job {id_job} não encontrado no banco (example)")
        return ""

    mensagem = job["mensagem"]

    # Simula algum processamento "pesado"
    time.sleep(2)

    resposta = "Response example to job " + id_job + " with message " + mensagem
    return resposta

# ========================================================================
