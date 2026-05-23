# CondoFix

Sistema de gestão de manutenção condominial.

## Tecnologias
- Python 3.10
- Flask
- SQLAlchemy (SQLite)
- Bootstrap 5
- Docker

## Como Executar

### Via Docker (Recomendado)
```bash
docker-compose up -d --build
```
Acesse em: `http://localhost:5000`

### Localmente
1. Crie um ambiente virtual: `python3 -m venv .venv`
2. Ative: `source .venv/bin/activate`
3. Instale as dependências: `pip install -r requirements.txt`
4. Execute: `python run.py`

## Credenciais Iniciais (Admin)
- **E-mail:** `admin@condofix.local`
- **Senha:** `admin@1234`

## Testes
```bash
docker exec -it condofix-app pytest -v
```
