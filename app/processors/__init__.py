# app/processors/ - Sub-projeto de processamento pesado
# =====================================================
# Código executado pelo consumer. processar_mensagem() é o ponto de entrada.

from app.processors.mensagem import processar_mensagem

_all_ = ["processar_mensagem"]

# =====================================================