# app/queue/producer.py - Enfileiramento de mensagens
# ====================================================

from app.queue.redis_client import get_redis, get_queue_name


# BEGIN CHANGE: permitir definir o processor via rota
def enqueue(id_job: str, processor: str = "mensagem") -> bool:
    """
    Adiciona job à fila Redis (LPUSH), incluindo o nome do processor.
    Formato do payload na fila: "<processor>:<id_job>".
    """
    r = get_redis()
    payload = f"{processor}:{id_job}"
    r.lpush(get_queue_name(), payload)
    return True
# END CHANGE: permitir definir o processor via rota

# ====================================================
