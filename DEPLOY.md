# Guia de Deploy - AI Agent Miraflores

Este guia detalha a configuração do servidor Ubuntu, systemd, banco de dados e GitHub Secrets.

---

## 1. Lista completa de GitHub Secrets

Configure em **Settings** → **Secrets and variables** → **Actions** → **New repository secret**:

| Secret | Obrigatório | Exemplo | Descrição |
|--------|-------------|---------|-----------|
| `MYSQL_HOST` | Sim | `10.0.0.5` | IP privado do servidor onde o MySQL está |
| `MYSQL_PORT` | Sim | `3306` | Porta do MySQL |
| `MYSQL_USER` | Sim | `ai_agent` | Usuário do banco |
| `MYSQL_PASSWORD` | Sim | `sua_senha_segura` | Senha do banco |
| `MYSQL_DATABASE` | Sim | `ai_agent_miraflores` | Nome do banco |
| `REDIS_HOST` | Sim | `localhost` ou `10.0.0.6` | IP do Redis |
| `REDIS_PORT` | Sim | `6379` | Porta do Redis |
| `API_KEY` | Não | `chave_lambda` | Chave para o Lambda (vazio se não usar) |
| `DEPLOY_HOST` | Sim | `meu-servidor.com` ou `1.2.3.4` | IP ou hostname do servidor Ubuntu |
| `DEPLOY_USER` | Sim | `ubuntu` | Usuário SSH |
| `DEPLOY_SSH_KEY` | Sim | (conteúdo do .pem) | Chave privada SSH completa |
| `DEPLOY_PATH` | Sim | `/home/ubuntu/Ai-Agent` | Caminho do projeto no servidor |

---

## 2. Banco de dados MySQL

**Sim, você precisa criar o banco e a tabela manualmente** (uma única vez).

### 2.1. Conectar ao MySQL

```bash
mysql -u root -p
```

### 2.2. Executar o script

No cliente MySQL, execute o conteúdo de `scripts/init_db.sql`:

```sql
CREATE DATABASE IF NOT EXISTS ai_agent_miraflores;
USE ai_agent_miraflores;

CREATE TABLE IF NOT EXISTS jobs (
    id_job VARCHAR(36) PRIMARY KEY,
    mensagem TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    resposta TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE INDEX idx_jobs_status ON jobs(status);
```

Ou, se o arquivo estiver no servidor:

```bash
mysql -u root -p < /caminho/para/Ai-Agent/scripts/init_db.sql
```

### 2.3. Criar usuário (recomendado)

Em vez de usar `root`, crie um usuário dedicado:

```sql
CREATE USER 'ai_agent'@'%' IDENTIFIED BY 'sua_senha_segura';
GRANT ALL PRIVILEGES ON ai_agent_miraflores.* TO 'ai_agent'@'%';
FLUSH PRIVILEGES;
```

Use `ai_agent` e a senha nos secrets `MYSQL_USER` e `MYSQL_PASSWORD`.

---

## 3. Configuração do servidor Ubuntu

### 3.1. Pré-requisitos

```bash
# Python 3.10+
sudo apt update
sudo apt install python3 python3-venv python3-pip -y

# Redis (se não estiver instalado)
sudo apt install redis-server -y
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

### 3.2. Criar diretório do projeto

```bash
mkdir -p /home/ubuntu/Ai-Agent
# Ajuste o caminho se usar outro usuário
```

### 3.3. Primeiro deploy (antes do GitHub Actions)

Faça o primeiro clone manualmente para criar o venv:

```bash
cd /home/ubuntu
git clone https://github.com/SEU_USUARIO/Ai-Agent.git
cd Ai-Agent

# Criar ambiente virtual e instalar dependências
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

O arquivo `.env` será criado pelo workflow de deploy. Se quiser testar antes, crie manualmente:

```bash
cp .env.example .env
nano .env  # Preencha os valores
```

---

## 4. Configuração do systemd

### 4.1. Editar os arquivos de serviço

Copie os arquivos e edite com seus valores:

```bash
sudo cp /home/ubuntu/Ai-Agent/deploy/ai-agent-api.service /etc/systemd/system/
sudo cp /home/ubuntu/Ai-Agent/deploy/ai-agent-worker.service /etc/systemd/system/
sudo nano /etc/systemd/system/ai-agent-api.service
sudo nano /etc/systemd/system/ai-agent-worker.service
```

Substitua em **ambos** os arquivos:

| Placeholder | Substituir por |
|-------------|----------------|
| `seu_usuario` | Seu usuário Linux (ex: `ubuntu`) |
| `/caminho/para/Ai-Agent` | Caminho real (ex: `/home/ubuntu/Ai-Agent`) |

Exemplo do arquivo `ai-agent-api.service` após editar:

```ini
[Unit]
Description=AI Agent API (FastAPI)
After=network.target redis-server.service mysql.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/Ai-Agent
Environment="PATH=/home/ubuntu/Ai-Agent/venv/bin"
ExecStart=/home/ubuntu/Ai-Agent/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 4.2. Habilitar e iniciar os serviços

```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-agent-api ai-agent-worker
sudo systemctl start ai-agent-api ai-agent-worker
```

### 4.3. Verificar status

```bash
sudo systemctl status ai-agent-api
sudo systemctl status ai-agent-worker
```

### 4.4. Comandos úteis

```bash
# Ver logs
sudo journalctl -u ai-agent-api -f
sudo journalctl -u ai-agent-worker -f

# Reiniciar
sudo systemctl restart ai-agent-api ai-agent-worker

# Parar
sudo systemctl stop ai-agent-api ai-agent-worker
```

---

## 5. Ordem recomendada de setup

1. **MySQL**: criar banco, tabela e usuário
2. **Redis**: instalar e iniciar
3. **Servidor**: criar diretório, clonar repo, criar venv, instalar deps
4. **Systemd**: copiar e editar serviços, habilitar e iniciar
5. **GitHub**: configurar todos os secrets
6. **Deploy**: fazer push na `main` ou executar o workflow manualmente

Após o primeiro deploy automático, o rsync atualizará o código. O venv permanece no servidor (não é sobrescrito). Se adicionar novas dependências no `requirements.txt`, execute no servidor:

```bash
cd /home/ubuntu/Ai-Agent
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart ai-agent-api ai-agent-worker
```
