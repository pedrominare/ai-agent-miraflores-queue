# app/processors/mensagem.py - Processamento de mensagens (sub-projeto pesado)
# ============================================================================
# Ponto de entrada: processar_mensagem(id_job). Toda a lógica pesada fica aqui.
# O consumer apenas chama esta função. Adicione novos módulos em processors/
# e importe/roteie conforme o input recebido.
# ============================================================================

import re
import time
import logging
from app.db.models import get_job

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _calcular(expressao: str) -> str | None:
    """
    Calculadora simples: extrai "X ou Y" da mensagem (ex: "2 + 3", "10 * 5").
    """
    match = re.search(r"(\d+)\s*([+\-/])\s(\d+)", expressao)
    if not match:
        return None
    a, op, b = int(match.group(1)), match.group(2), int(match.group(3))
    if op == "+":
        return str(a + b)
    if op == "-":
        return str(a - b)
    if op == "*":
        return str(a * b)
    if op == "/":
        return str(a // b) if b else None
    return None


def processar_mensagem(id_job: str) -> str:
    """
    Processa o job. Obtém input, roteia para a lógica adequada, retorna resposta.
    Adicione aqui roteamento por tipo de mensagem ou integre novos processadores.
    """
    job = get_job(id_job)
    if not job:
        logger.warning(f"Job {id_job} não encontrado no banco")
        return ""

    mensagem = job["mensagem"]

    # Exemplo: rotear por input. Aqui pode ir logica pesada (IA, relatorios, etc.)
    resultado_calc = _calcular(mensagem)

    # Simula processamento pesado
    time.sleep(3)

    if resultado_calc:
        resposta = f"Olá, eu recebi e fiz uma conta louca aqui? Sua mensagem: '{mensagem}'. Resultado: {resultado_calc}"
    else:
        resposta = f"Olá, eu recebi e fiz uma conta louca aqui? Sua mensagem: '{mensagem}'. (Não achei conta no formato 'X op Y', ex: 2 + 3)"
    return resposta

# ============================================================================