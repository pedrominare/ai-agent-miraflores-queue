# app/db/models.py - Operações de banco (jobs)
# ============================================

import uuid
from app.db.connection import get_cursor


def create_job(mensagem: str) -> str:
    """Cria job no banco e retorna id_job."""
    id_job = str(uuid.uuid4())
    with get_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO jobs (id_job, mensagem, status)
            VALUES (%s, %s, 'pending')
            """,
            (id_job, mensagem),
        )
    return id_job


def get_job(id_job: str) -> dict | None:
    """Busca job por id_job."""
    with get_cursor() as cursor:
        cursor.execute(
            "SELECT id_job, mensagem, status, resposta, created_at, updated_at FROM jobs WHERE id_job = %s",
            (id_job,),
        )
        return cursor.fetchone()


def update_job_status(id_job: str, status: str, resposta: str | None = None):
    """Atualiza status e opcionalmente resposta do job."""
    with get_cursor() as cursor:
        if resposta is not None:
            cursor.execute(
                "UPDATE jobs SET status = %s, resposta = %s, updated_at = NOW() WHERE id_job = %s",
                (status, resposta, id_job),
            )
        else:
            cursor.execute(
                "UPDATE jobs SET status = %s, updated_at = NOW() WHERE id_job = %s",
                (status, id_job),
            )

# ============================================
