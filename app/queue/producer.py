# app/queue/producer.py - Enfileiramento de mensagens
# ====================================================

from app.queue.redis_client import get_redis, get_queue_name


def enqueue(id_job: str) -> bool:
    """Adiciona id_job à fila Redis (LPUSH)."""
    r = get_redis()
    r.lpush(get_queue_name(), id_job)
    return True

# ====================================================
