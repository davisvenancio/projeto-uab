# Relatório de Inspeção de Segurança - Sistema CondoFix

## 1. Resumo Executivo

Esta inspeção superficial de cibersegurança foi realizada nos arquivos do diretório `src/` do sistema CondoFix, seguindo as diretrizes do OWASP Top 10 e melhores práticas de desenvolvimento seguro. A análise identificou falhas estruturais importantes que podem comprometer a integridade dos dados e a segurança dos usuários.

### 1.1. Contagem de Achados por Severidade

| Severidade | Quantidade |
| :--- | :--- |
| 🔴 Crítica | 1 |
| 🟠 Alta | 2 |
| 🟡 Média | 2 |
| 🔵 Baixa | 1 |
| **Total** | **6** |

### 1.2. Top 5 Ações Mais Urgentes

1.  **Implementar Proteção Anti-CSRF:** Ativar o Flask-WTF em todos os formulários POST.
2.  **Configurar Cabeçalhos de Segurança:** Utilizar Flask-Talisman para implementar CSP, HSTS e proteção contra XSS.
3.  **Reforçar Segurança de Cookies:** Configurar os flags `HttpOnly`, `Secure` e `SameSite` para a sessão.
4.  **Melhorar Validação de Uploads:** Validar tipos MIME reais (magic bytes) e não apenas extensões.
5.  **Sanitização de Entradas:** Implementar validação rigorosa de tipos e tamanhos em todas as rotas de recepção de dados.

---

## 2. Detalhamento das Vulnerabilidades

### VULN-001: Ausência de Proteção contra CSRF (Cross-Site Request Forgery)
- **Localização:** Global (`requirements.txt`, `src/views/*.py`)
- **Descrição:** O sistema não utiliza tokens CSRF para validar requisições de alteração de estado (POST). Um atacante pode induzir um usuário autenticado a executar ações indesejadas (ex: abrir chamados, deletar técnicos) via sites maliciosos.
- **Evidência:** `requirements.txt` não contém `Flask-WTF` e os formulários nos templates não enviam tokens.
- **Impacto Potencial:** Execução de ações em nome do usuário sem seu consentimento.
- **Severidade:** 🔴 Crítica
- **Recomendação:** Instalar `Flask-WTF` e inicializar `CSRFProtect(app)` no `src/__init__.py`. Adicionar `{{ form.csrf_token }}` em todos os templates.
- **Referências:** OWASP A01:2021, CWE-352.

### VULN-002: Ausência de Cabeçalhos de Segurança HTTP
- **Localização:** `src/__init__.py`
- **Descrição:** A aplicação não envia cabeçalhos essenciais como `Content-Security-Policy` (CSP), `X-Content-Type-Options` ou `Strict-Transport-Security` (HSTS).
- **Evidência:** A factory function `create_app()` não utiliza middleware de segurança como o `Flask-Talisman`.
- **Impacto Potencial:** Facilita ataques de XSS, Clickjacking e interceptação de tráfego.
- **Severidade:** 🟠 Alta
- **Recomendação:** Implementar `Flask-Talisman(app)` com uma política de CSP restritiva.
- **Referências:** OWASP A02:2021, CWE-693.

### VULN-003: Validação Insuficiente de Upload de Imagens
- **Localização:** `src/services/image_service.py`, Função `processar_imagem`, Linha 7.
- **Descrição:** A validação baseia-se apenas na extensão do arquivo fornecida pelo usuário, que pode ser facilmente burlada (ex: um script PHP renomeado para .jpg).
- **Evidência:** 
  ```python
  extensao = arquivo_form.filename.split(".")[-1].lower()
  if extensao not in allowed_extensions:
  ```
- **Impacto Potencial:** Armazenamento de arquivos maliciosos ou execução de código remoto (RCE) se o servidor processar esses arquivos de forma insegura.
- **Severidade:** 🟠 Alta
- **Recomendação:** Utilizar bibliotecas como `python-magic` para verificar os "magic bytes" do arquivo e validar o tipo MIME real.
- **Referências:** OWASP A03:2021, CWE-434.

### VULN-004: Cookies de Sessão Inseguros
- **Localização:** `src/config.py` ou `src/__init__.py`
- **Descrição:** Não há configuração explícita para garantir que os cookies de sessão sejam protegidos contra acesso via script (`HttpOnly`) ou interceptação (`Secure`).
- **Evidência:** Ausência de configurações como `SESSION_COOKIE_HTTPONLY = True` e `SESSION_COOKIE_SECURE = True` na classe `Config`.
- **Impacto Potencial:** Sequestro de sessão via XSS ou interceptação em redes não criptografadas.
- **Severidade:** 🟡 Média
- **Recomendação:** Adicionar `SESSION_COOKIE_HTTPONLY = True`, `SESSION_COOKIE_SECURE = True` (em produção) e `SESSION_COOKIE_SAMESITE = 'Lax'` às configurações.
- **Referências:** OWASP A07:2021, CWE-614.

### VULN-005: Tratamento de Exceções Genérico
- **Localização:** `src/views/auth_view.py`, Função `cadastro`, Linha 74.
- **Descrição:** O uso de blocos `try-except` genéricos sem log detalhado do erro oculta falhas críticas e dificulta a depuração e monitoramento de incidentes.
- **Evidência:**
  ```python
  except Exception:
      db.session.rollback()
      flash("Erro interno. Tente novamente.")
  ```
- **Impacto Potencial:** Dificuldade em identificar tentativas de ataque ou falhas de integridade de dados (A09).
- **Severidade:** 🟡 Média
- **Recomendação:** Capturar exceções específicas (ex: `IntegridadeError`) e logar o traceback completo (sem expor ao usuário) para auditoria.
- **Referências:** OWASP A10:2021, CWE-755.

### VULN-006: Uso de Segredo de Sessão Fraco/Padrão
- **Localização:** `.env` (referenciado em `src/config.py`)
- **Descrição:** O valor de `SECRET_KEY` no ambiente é um placeholder previsível.
- **Evidência:** `SECRET_KEY=temporary_secret_key_change_me` identificado no arquivo `.env`.
- **Impacto Potencial:** Falsificação de cookies de sessão e bypass de autenticação.
- **Severidade:** 🔵 Baixa (Depende do ambiente)
- **Recomendação:** Gerar uma chave criptograficamente forte utilizando `os.urandom(24)` e nunca utilizar valores padrão.
- **Referências:** OWASP A02:2021, CWE-330.
