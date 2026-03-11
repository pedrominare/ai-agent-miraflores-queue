-- scripts/init_db.sql - Criação do banco e tabela jobs
-- ====================================================

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

-- Índice para consultas por status (opcional)
CREATE INDEX idx_jobs_status ON jobs(status);

-- ====================================================
