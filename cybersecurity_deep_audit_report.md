# Relatório de Inspeção Profunda de Cibersegurança - CondoFix

Este relatório apresenta os resultados da auditoria de segurança realizada nos arquivos do diretório `src`, fundamentada nas melhores práticas de desenvolvimento seguro e no OWASP Top 10.

---

## 1. Falta de Proteção contra CSRF (Cross-Site Request Forgery)
- **Localização:** Global (`src/__init__.py`) e em todos os formulários POST em `src/templates/`.
- **Descrição:** O aplicativo não implementava tokens de validação para requisições que alteram estado, permitindo ataques onde um usuário autenticado é induzido a executar ações maliciosas.
- **Evidência:** Ausência de `CSRFProtect` na inicialização do Flask e falta de campos de token nos arquivos `.html`.
- **Impacto:** Potencial alteração de dados, deleção de usuários ou escalonamento de privilégios via sequestro de sessão.
- **Severidade:** **Crítica**
- **Status:** **Corrigido** (Implementado `Flask-WTF` e adicionado `csrf_token()` em todos os formulários).

## 2. Credenciais Hardcoded no Seed do Banco de Dados
- **Localização:** `src/models.py`, função `seed_db`.
- **Descrição:** Senhas administrativas e de usuários de teste estavam escritas diretamente no código-fonte.
- **Evidência:** `admin.definir_senha("admin@1234")`
- **Impacto:** Exposição de credenciais de alto privilégio caso o código seja vazado ou acessado por terceiros.
- **Severidade:** **Alta**
- Status: **Corrigido** (Migrado para variáveis de ambiente `ADMIN_PASSWORD` e `MORADOR_PASSWORD`).

## 3. Configuração Insegura de Cookies (Falta de Flag Secure)
- **Localização:** `src/config.py`, classe `Config`.
- **Descrição:** O cookie de sessão não estava marcado como `Secure`, permitindo transmissão via HTTP puro.
- **Evidência:** `SESSION_COOKIE_SECURE = False`
- **Impacto:** Interceptação de sessão em ataques Man-in-the-Middle (MitM).
- **Severidade:** **Média**
- **Status:** **Corrigido** (Alterado para `True`).

## 4. Vulnerabilidade de Negação de Serviço (DoS) no Upload
- **Localização:** `src/services/image_service.py`, função `processar_imagem`.
- **Descrição:** O arquivo era lido inteiramente para a memória RAM antes de validar seu tamanho.
- **Evidência:** `conteudo_bytes = arquivo_form.read()` seguido de validação de tamanho.
- **Impacto:** Esgotamento de recursos do servidor (RAM) através do envio de arquivos gigantes.
- **Severidade:** **Média**
- **Status:** **Corrigido** (Adicionada validação de tamanho via `seek/tell` antes do `read`).

## 5. Enumeração de Usuários
- **Localização:** `src/views/auth_view.py`, rota `/cadastro`.
- **Descrição:** Mensagens de erro específicas confirmavam se um e-mail já existia na base.
- **Evidência:** `flash("E-mail já cadastrado.")`
- **Impacto:** Facilita a descoberta de contas para ataques de força bruta direcionados.
- **Severidade:** **Média/Baixa**
- **Status:** **Corrigido** (Mensagens tornadas genéricas e log de aviso implementado).

## 6. Ausência de Cabeçalhos de Segurança HTTP
- **Localização:** Global (`src/__init__.py`).
- **Descrição:** Falta de proteção contra Clickjacking, Sniffing de MIME e XSS persistente via headers.
- **Evidência:** Ausência de CSP, HSTS e X-Frame-Options.
- **Impacto:** Maior superfície de ataque para vetores de frontend.
- **Severidade:** **Média**
- **Status:** **Corrigido** (Integrado `Flask-Talisman`).

---

**Auditor:** Gemini CLI
**Data:** 24 de Maio de 2026
**Nível de Profundidade:** Profunda
