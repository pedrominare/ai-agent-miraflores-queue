# Segurança

## Variáveis sensíveis

- **Nenhuma credencial é armazenada no código.** Todas as configurações vêm de variáveis de ambiente.
- O arquivo `.env` está no `.gitignore` e não deve ser commitado.
- Em repositórios públicos: use **GitHub Secrets** para MySQL (host, user, password, database), Redis, API_KEY e deploy (Settings → Secrets and variables → Actions).

## Reportar vulnerabilidades

Se encontrar uma vulnerabilidade, abra uma issue ou entre em contato diretamente.
