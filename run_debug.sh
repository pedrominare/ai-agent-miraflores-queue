#!/bin/bash
# scripts/run_debug.sh - Roda API e Worker em modo debug com saída em um único terminal
# ================================================================================
# Uso: ./scripts/run_debug.sh   (ou bash scripts/run_debug.sh)
# Pare os serviços systemd antes: sudo systemctl stop ai-agent-api ai-agent-worker
# ===============================================================================

# Diretório do script e do projeto
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
INITIAL_PWD="$PWD"

# Se app não está em PROJECT_DIR, usar o diretório de onde o script foi chamado
if [ ! -d "$PROJECT_DIR/app" ] && [ -d "$INITIAL_PWD/app" ]; then
    PROJECT_DIR="$INITIAL_PWD"
fi

[ ! -d "$PROJECT_DIR/app" ] && echo "Erro: pasta app não encontrada. PROJECT_DIR=$PROJECT_DIR | PWD=$INITIAL_PWD" && exit 1

cd "$PROJECT_DIR" || exit 1

# Venv: preferir ./venv, senão ~/venvs/py314
if [ -d "$PROJECT_DIR/venv" ]; then
    source "$PROJECT_DIR/venv/bin/activate"
elif [ -d "$HOME/venvs/py314" ]; then
    source "$HOME/venvs/py314/bin/activate"
else
    echo "Erro: nenhum venv encontrado (venv ou ~/venvs/py314)"
    exit 1
fi

# Carregar .env se existir
[ -f "$PROJECT_DIR/.env" ] && set -a && source "$PROJECT_DIR/.env" && set +a

# Python encontra o módulo app
export PYTHONPATH="$PROJECT_DIR"

# Ctrl+C mata API e Worker (processos filhos do script)
trap 'pkill -P $$ 2>/dev/null; exit' INT TERM

echo "=== API + Worker em modo debug (Ctrl+C para parar) ==="
echo "Projeto: $PROJECT_DIR"
echo ""

# Sem --reload: evita 99% CPU (watchfiles monitora o disco constantemente)
(cd "$PROJECT_DIR" && PYTHONPATH="$PROJECT_DIR" uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level debug) 2>&1 | sed 's/^/[API] /' &
(cd "$PROJECT_DIR" && PYTHONPATH="$PROJECT_DIR" PYTHONUNBUFFERED=1 python run_worker.py) 2>&1 | sed 's/^/[WORKER] /' &

wait

# ================================================================================