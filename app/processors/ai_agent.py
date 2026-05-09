# app/processors/cock_ascii.py - Processamento da rota /cock-ascii
# ========================================================================
# Processor separado para a rota /cock-ascii. Mantém a lógica simples
# e isolada, podendo evoluir de forma independente do processar_mensagem.
# ========================================================================

import time
import logging
import subprocess
from pathlib import Path
import sys
from app.config import AI_AGENT_SUBPROCESS_TIMEOUT
from app.db.models import get_job

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REPO = Path("/home/ollama/ai-agent-ollama").resolve()
AI_SRC = REPO / "ai_src"


def processar_ai_agent(id_job: str) -> str:
    """
    Processa o job criado pela rota /ai-agent.
    Se existir o script externo, envia a mensagem do job como pergunta (1º argumento CLI).
    Caso contrário, resposta simulada (compatível com ambientes sem o agente instalado).
    """
    job = get_job(id_job)
    if not job:
        logger.warning(f"Job {id_job} não encontrado no banco (ai-agent)")
        return ""

    mensagem = job["mensagem"]

    caminho_script = str(AI_SRC / "main.py")
    if Path(caminho_script).is_file():
        try:
            return executar_python_subprocess(
                caminho_script,
                args=['ask', mensagem, '--langchain'],
                timeout=AI_AGENT_SUBPROCESS_TIMEOUT,
            )
        except (RuntimeError, subprocess.TimeoutExpired) as exc:
            logger.exception("Subprocess do agente falhou para job %s", id_job)
            return f"Erro ao consultar o agente: {exc}"

    time.sleep(2)
    resposta = "Response ai-agent to job " + id_job + " with message " + mensagem
    return resposta


def executar_python_subprocess(
    caminho_script: str,
    args: list[str] | None = None,
    timeout: float | None = None,
) -> str:
    """
    Executa outro arquivo Python num processo filho (mesmo interpretador que este app).
    Retorna o stdout (texto). Em código de saída != 0 ou timeout, levanta exceção.
    """
    cmd = [sys.executable, caminho_script, *(args or [])]
    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        logger.error("Timeout ao executar %s: %s", caminho_script, exc)
        raise
    if completed.returncode != 0:
        err = (completed.stderr or completed.stdout or "").strip()
        logger.error("Script %s falhou (%s): %s", caminho_script, completed.returncode, err)
        raise RuntimeError(
            f"Script externo terminou com código {completed.returncode}: {err}"
        )
    return (completed.stdout or "").strip()

# ========================================================================
