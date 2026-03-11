# app/db/connection.py - Conexão MySQL
# =====================================

import mysql.connector
from mysql.connector import Error
from contextlib import contextmanager

from app.config import (
    MYSQL_HOST,
    MYSQL_PORT,
    MYSQL_USER,
    MYSQL_PASSWORD,
    MYSQL_DATABASE,
)


def get_connection():
    """Retorna conexão MySQL."""
    return mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
    )


@contextmanager
def get_cursor():
    """Context manager para cursor MySQL."""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        yield cursor
        conn.commit()
    except Error:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

# =====================================
