# app/worker/consumer.py - Consumidor da fila Redis
# ==================================================
# Apenas orquestra: consome fila, chama processar_mensagem(), atualiza status.
# Toda a lógica pesada fica em app/processors/.

import time
import logging
from app.queue.redis_client import get_redis, get_queue_name
from app.db.models import update_job_status
from app.processors.mensagem import processar_mensagem
from app.processors.cock_ascii import processar_cock_ascii

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


PROCESSORS = {
    "mensagem": processar_mensagem,
    "cock_ascii": processar_cock_ascii,
}


def _parse_payload(raw_payload: str) -> tuple[str, str]:
    """
    Decodifica o payload vindo da fila.
    Formato esperado: "<processor>:<id_job>".
    Mantém compatibilidade com payloads antigos contendo apenas o id_job.
    """
    if ":" not in raw_payload:
        return "mensagem", raw_payload
    processor, id_job = raw_payload.split(":", 1)
    return processor or "mensagem", id_job


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

            _, raw_payload = result
            processor_name, id_job = _parse_payload(raw_payload)
            logger.info(f"Processando job {id_job} com processor '{processor_name}'")

            try:
                update_job_status(id_job, "processing")
                processor_fn = PROCESSORS.get(processor_name, processar_mensagem)
                resposta = processor_fn(id_job)
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