# app/worker/consumer.py - Consumidor da fila Redis
# ==================================================
# Processa mensagens da fila. Ponto de integração futuro para o agente de IA.

import time
import logging
from app.queue.redis_client import get_redis, get_queue_name
from app.db.models import get_job, update_job_status

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def processar_mensagem(id_job: str) -> str:
    """
    Processa a mensagem do job.
    TODO: Integrar agente de IA aqui. Por ora, retorna resposta simulada.
    """
    job = get_job(id_job)
    if not job:
        logger.warning(f"Job {id_job} não encontrado no banco")
        return ""

    mensagem = job["mensagem"]
    # Placeholder: resposta simulada. Substituir pela chamada ao agente de IA.
    resposta = f"Recebi sua mensagem: '{mensagem}'. (Resposta simulada - agente de IA será integrado aqui)"
    return resposta


def run_worker():
    """Loop principal do worker. Consome fila com BRPOP (bloqueante)."""
    r = get_redis()
    queue = get_queue_name()

    logger.info(f"Worker iniciado. Aguardando mensagens na fila '{queue}'...")

    while True:
        try:
            # BRPOP bloqueia até chegar mensagem (timeout 5s para permitir graceful shutdown)
            result = r.brpop(queue, timeout=5)
            if result is None:
                continue

            _, id_job = result
            logger.info(f"Processando job {id_job}")

            try:
                update_job_status(id_job, "processing")
                resposta = processar_mensagem(id_job)
                update_job_status(id_job, "completed", resposta=resposta)
                logger.info(f"Job {id_job} concluído")
            except Exception as e:
                logger.exception(f"Erro ao processar job {id_job}: {e}")
                update_job_status(id_job, "failed")

        except KeyboardInterrupt:
            logger.info("Worker encerrado")
            break
        except Exception as e:
            logger.exception(f"Erro no worker: {e}")
            time.sleep(5)

# ==================================================


if __name__ == "__main__":
    run_worker()
