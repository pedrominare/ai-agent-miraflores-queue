# app/queue/redis_client.py - Cliente Redis
# =========================================

import redis
from app.config import REDIS_HOST, REDIS_PORT, REDIS_QUEUE_NAME


def get_redis():
    """Retorna cliente Redis."""
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


def get_queue_name():
    """Retorna nome da fila."""
    return REDIS_QUEUE_NAME

# =========================================
