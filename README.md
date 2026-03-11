# AI Agent Miraflores

API FastAPI que recebe mensagens de um Lambda AWS, enfileira em Redis e processa via worker em background. Arquitetura preparada para integração futura com agente de IA.

---

## Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura](#arquitetura)
3. [Desenvolvimento do Projeto](#desenvolvimento-do-projeto)
4. [Estrutura de Diretórios](#estrutura-de-diretórios)
5. [Funcionamento Detalhado](#funcionamento-detalhado)
6. [Instalação e Configuração](#instalação-e-configuração)
7. [Segurança e GitHub Secrets](#segurança-e-github-secrets)
8. [Endpoints da API](#endpoints-da-api)
9. [Deploy em Produção](#deploy-em-produção)
10. [Integração com Agente de IA](#integração-com-agente-de-ia)

---

## Visão Geral

O projeto foi desenvolvido para atuar como **backend de processamento assíncrono** de mensagens. Um Lambda AWS envia mensagens via HTTP; a API recebe, registra no banco e enfileira para processamento. O Lambda recebe imediatamente um `id_job` e pode consultar o status e a resposta posteriormente.

**Características principais:**

- **Desacoplamento**: Lambda não precisa esperar o processamento; retorna rápido com `id_job`.
- **Fila local**: Redis como fila de mensagens (sem SQS).
- **Persistência**: MySQL armazena jobs, status e respostas.
- **Escalável**: Múltiplos workers podem consumir a mesma fila.

---

## Arquitetura

```
┌─────────────┐                    ┌─────────────────────────────────────────────────────────┐
│   Lambda    │                    │              Servidor Ubuntu (24/7)                     │
│   (AWS)     │                    │                                                         │
└──────┬──────┘                    │  ┌─────────────┐    ┌─────────────┐                     │
       │                           │  │   FastAPI    │───►│   Redis     │                     │
       │  POST /api/mensagens      │  │   (API)      │    │   (fila)    │                     │
       │  {"mensagem": "olá"}      │  └──────┬───────┘    └──────┬──────┘                     │
       │                           │         │                   │                            │
       │  ◄── {"id_job": "uuid"}   │         │                   │ BRPOP                      │
       │                           │         │                   ▼                            │
       │  GET /api/jobs/{id_job}   │         │           ┌───────────────┐                    │
       │  ◄── {"status", "resposta"}         │           │    Worker     │                    │
       │                           │         │           │  (consumidor)  │                    │
       │                           │         │           └───────┬───────┘                    │
       │                           │         │                   │                            │
       │                           │         ▼                   ▼                            │
       │                           │  ┌─────────────────────────────────────┐                 │
       │                           │  │         MySQL (ai_agent_miraflores) │                 │
       │                           │  │  jobs: id_job, mensagem, status,    │                 │
       │                           │  │         resposta, created_at, etc.  │                 │
       │                           │  └─────────────────────────────────────┘                 │
       │                           └─────────────────────────────────────────────────────────┘
```

**Fluxo resumido:**

1. Lambda envia `POST` com a mensagem.
2. FastAPI cria o job no MySQL (status `pending`), enfileira `id_job` no Redis e retorna `id_job`.
3. Worker consome a fila (BRPOP), atualiza status para `processing`, processa a mensagem e grava a resposta (status `completed`).
4. Lambda consulta `GET /api/jobs/{id_job}` para obter status e resposta.

---

## Desenvolvimento do Projeto

### Decisões de design

| Decisão | Motivo |
|---------|--------|
| **FastAPI** | Framework moderno, tipado, documentação automática (Swagger). |
| **Redis como fila** | Simples, local, sem dependência de SQS. Uso de LPUSH/BRPOP (FIFO). |
| **MySQL** | Banco relacional já disponível no servidor; jobs precisam de persistência. |
| **Worker separado** | Processamento assíncrono; API responde rápido sem bloquear. |

### Banco de dados: ai_agent_miraflores

O banco foi nomeado `ai_agent_miraflores` para identificar o projeto e o contexto de uso. A tabela `jobs` armazena:

- `id_job`: UUID do job (chave primária).
- `mensagem`: Texto recebido do Lambda.
- `status`: `pending` → `processing` → `completed` ou `failed`.
- `resposta`: Resposta gerada pelo processamento (preenchida quando `completed`).
- `created_at`, `updated_at`: Timestamps.

### Fila Redis

- **Estrutura**: Lista Redis (LPUSH para enfileirar, BRPOP para consumir).
- **Nome da fila**: `mensagens_fila` (configurável via `.env`).
- **Conteúdo**: Apenas o `id_job` (string UUID); os dados completos ficam no MySQL.

---

## Estrutura de Diretórios

```
Ai-Agent/
├── app/
│   ├── __init__.py
│   ├── main.py              # Aplicação FastAPI, registro de rotas
│   ├── config.py            # Variáveis de ambiente (Redis, MySQL, API)
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py        # POST /api/mensagens, GET /api/jobs/{id_job}
│   ├── queue/
│   │   ├── __init__.py
│   │   ├── redis_client.py  # Conexão Redis
│   │   └── producer.py      # Enfileiramento (LPUSH)
│   ├── worker/
│   │   ├── __init__.py
│   │   └── consumer.py      # Loop BRPOP, processamento, atualização MySQL
│   ├── db/
│   │   ├── __init__.py
│   │   ├── connection.py    # Conexão MySQL, context manager
│   │   └── models.py        # create_job, get_job, update_job_status
│   └── schemas/
│       ├── __init__.py
│       └── mensagem.py      # Pydantic: MensagemInput, MensagemResponse, JobStatusResponse
├── scripts/
│   └── init_db.sql         # Criação do banco ai_agent_miraflores e tabela jobs
├── deploy/
│   ├── ai-agent-api.service    # Systemd para API
│   └── ai-agent-worker.service # Systemd para Worker
├── run_api.py              # Ponto de entrada da API
├── run_worker.py           # Ponto de entrada do Worker
├── requirements.txt
├── .env.example          # Template (sem valores reais)
├── .gitignore
├── .github/workflows/    # CI e exemplo de deploy com secrets
├── SECURITY.md
└── README.md
```

---

## Funcionamento Detalhado

### 1. Recebimento da mensagem (API)

- Rota `POST /api/mensagens` recebe `{"mensagem": "olá"}`.
- Validação via Pydantic (`MensagemInput`).
- Opcional: validação de `X-API-Key` se `API_KEY` estiver definida no `.env`.
- `create_job(mensagem)` insere no MySQL com status `pending`.
- `enqueue(id_job)` faz LPUSH na fila Redis.
- Resposta: `{"id_job": "uuid", "status": "pending"}`.

### 2. Processamento (Worker)

- Loop infinito com `BRPOP` (bloqueante) na fila Redis.
- Ao receber um `id_job`, busca o job no MySQL.
- Atualiza status para `processing`.
- Chama `processar_mensagem(id_job)` — hoje com resposta simulada; futuro: agente de IA.
- Atualiza status para `completed` e grava `resposta` no MySQL.
- Em caso de erro: status `failed`.

### 3. Consulta de status (API)

- Rota `GET /api/jobs/{id_job}` busca o job no MySQL.
- Retorna `id_job`, `status`, `mensagem`, `resposta` (quando houver).

---

## Instalação e Configuração

### Pré-requisitos

- Python 3.14
- Redis instalado e em execução
- MySQL instalado e em execução

## Segurança e GitHub Secrets

**Nenhuma variável sensível fica no código.** O projeto usa `os.getenv()` para ler configurações; os valores vêm de ambiente ou arquivo `.env` (gitignored).

### GitHub Secrets

Configure todos os secrets para o workflow de deploy funcionar:

### Como o deploy funciona

O workflow `.github/workflows/deploy.yml` executa **automaticamente em cada push na branch `main`** (ou manualmente em Actions → Deploy → Run workflow). Ele:

1. Sincroniza o código para o servidor via rsync (exclui `.env`, `venv`, `.git`)
2. Cria o `.env` a partir dos secrets e envia via SCP
3. Reinicia os serviços `ai-agent-api` e `ai-agent-worker`

**Primeira vez:** crie o diretório no servidor (ex: `mkdir -p /home/usuario/Ai-Agent`) ou use um path existente. O rsync criará o conteúdo.


## Endpoints da API

### POST /api/mensagens

Recebe a mensagem do Lambda e cria o job.

**Request:**
```json
{
  "mensagem": "olá"
}
```

**Headers (opcional):** `X-API-Key: sua_chave`

**Response (201):**
```json
{
  "id_job": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending"
}
```

### GET /api/jobs/{id_job}

Consulta status e resposta do job.

**Response (200) — em processamento:**
```json
{
  "id_job": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "mensagem": "olá",
  "resposta": null
}
```

**Response (200) — concluído:**
```json
{
  "id_job": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "mensagem": "olá",
  "resposta": "Recebi sua mensagem: 'olá'. (Resposta simulada - agente de IA será integrado aqui)"
}
```

**Response (404):** Job não encontrado.

### GET /health

Health check para monitoramento.

**Response (200):**
```json
{
  "status": "ok"
}
```

---

## Deploy em Produção

Para rodar 24/7 no Ubuntu com systemd, consulte o guia completo em **[DEPLOY.md](DEPLOY.md)**, que inclui:

- Lista completa de GitHub Secrets
- Criação do banco e tabela MySQL
- Configuração do systemd passo a passo
- Ordem recomendada de setup

---

## Integração com Agente de IA

O ponto de integração está em `app/worker/consumer.py`, na função `processar_mensagem()`:

```python
def processar_mensagem(id_job: str) -> str:
    job = get_job(id_job)
    mensagem = job["mensagem"]
    # TODO: Chamar agente de IA aqui
    # resposta = agente.processar(mensagem)
    resposta = f"Recebi sua mensagem: '{mensagem}'..."  # Placeholder
    return resposta
```

Substitua a lógica de placeholder pela chamada ao seu agente de IA. A função deve retornar a string de resposta que será gravada no campo `resposta` da tabela `jobs` e exposta ao Lambda via `GET /api/jobs/{id_job}`.
