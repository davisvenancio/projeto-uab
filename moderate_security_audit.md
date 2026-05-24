# Relatório de Auditoria de Cibersegurança - Sistema CondoFix (Nível Moderado)

## 1. Resumo Executivo

Este documento apresenta os resultados de uma inspeção de cibersegurança com nível de profundidade **MODERADA** realizada nos componentes do diretório `src/`. A auditoria focou no OWASP Top 10 e em padrões de desenvolvimento seguro. Foram identificadas falhas que permitem a execução de ações não autorizadas (CSRF), exposição a ataques de injeção visual (XSS) e riscos de integridade de dados.

### 1.1. Contagem de Achados por Severidade

| Severidade | Quantidade |
| :--- | :--- |
| 🔴 Crítica | 1 |
| 🟠 Alta | 3 |
| 🟡 Média | 3 |
| 🔵 Baixa | 1 |
| **Total** | **8** |

### 1.2. Top 5 Ações Mais Urgentes

1.  **Proteção contra CSRF:** Habilitar globalmente o `Flask-WTF` para mitigar ataques de falsificação de requisição.
2.  **Imposição de Headers de Segurança:** Implementar `Flask-Talisman` para CSP, HSTS e prevenção de sniffing de tipos.
3.  **Validação Robusta de Arquivos:** Substituir validação por extensão por verificação de assinatura de arquivos (magic bytes).
4.  **Política de Complexidade de Senha:** Implementar regras de entropia no cadastro para mitigar ataques de força bruta.
5.  **Gerenciamento de Segredos:** Garantir que o `SECRET_KEY` e senhas padrão de seed sejam rotacionados e protegidos.

---

## 2. Detalhamento das Vulnerabilidades

### VULN-001: Ausência Global de Proteção contra CSRF (Cross-Site Request Forgery)
- **Localização:** Global (`src/views/*.py`, `src/templates/*.html`)
- **Descrição:** Requisições de estado (POST) não exigem tokens de validação. Um atacante pode criar um formulário oculto em um site malicioso para submeter chamados ou excluir usuários caso a vítima tenha uma sessão ativa.
- **Evidência:** Arquivo `src/views/chamados_view.py` não realiza verificação de token em rotas POST.
- **Impacto Potencial:** Execução de transações financeiras (registro de custo) ou administrativas em nome de terceiros.
- **Severidade:** 🔴 Crítica
- **Recomendação:** Instalar `Flask-WTF`, configurar `CSRFProtect(app)` e injetar `{{ form.csrf_token }}` nos templates.
- **Referências:** OWASP A01:2021, CWE-352.

### VULN-002: Ausência de Cabeçalhos de Segurança (Hardening HTTP)
- **Localização:** `src/__init__.py`, Função `create_app`.
- **Descrição:** A aplicação não utiliza cabeçalhos como `Content-Security-Policy` (CSP) ou `X-Frame-Options`, expondo-a a Clickjacking e XSS persistente.
- **Evidência:** Respostas HTTP carecem de diretivas de proteção de navegação.
- **Impacto Potencial:** Roubo de tokens de sessão e sequestro de UI.
- **Severidade:** 🟠 Alta
- **Recomendação:** Utilizar o módulo `Flask-Talisman` com configurações de CSP restritivas.
- **Referências:** OWASP A05:2021, CWE-693.

### VULN-003: Validação de Upload por Lista Branca de Extensão (Bypass de Integridade)
- **Localização:** `src/services/image_service.py`, Função `processar_imagem`, Linha 7.
- **Descrição:** A validação confia no nome do arquivo enviado pelo cliente. Um atacante pode renomear um script malicioso para `.jpg`.
- **Evidência:** 
  ```python
  extensao = arquivo_form.filename.split(".")[-1].lower()
  if extensao not in allowed_extensions:
  ```
- **Impacto Potencial:** Armazenamento de webshells ou arquivos que exploram vulnerabilidades de processamento de imagem no servidor.
- **Severidade:** 🟠 Alta
- **Recomendação:** Validar o cabeçalho binário do arquivo utilizando bibliotecas como `python-magic`.
- **Referências:** OWASP A08:2021, CWE-434.

### VULN-004: Credenciais Administrativas Padrão em Código (Seed)
- **Localização:** `src/models.py`, Função `seed_db`, Linhas 67-73.
- **Descrição:** Senhas administrativas fixas em código de inicialização são frequentemente esquecidas e exploradas.
- **Evidência:**
  ```python
  if not db.session.query(Usuario).filter_by(email="admin@condofix.local").first():
      admin = Usuario(nome="Administrador", email="admin@condofix.local", perfil="admin")
      admin.definir_senha("admin@1234")
  ```
- **Impacto Potencial:** Acesso administrativo imediato por qualquer pessoa com acesso ao repositório ou conhecimento do padrão.
- **Severidade:** 🟠 Alta
- **Recomendação:** Utilizar variáveis de ambiente para a senha inicial ou forçar a troca no primeiro login.
- **Referências:** OWASP A07:2021, CWE-1391.

### VULN-005: Exposição de Dados em Logs (A09 - Falha de Monitoramento)
- **Localização:** `src/views/chamados_view.py`, Função `background_processar_imagem`, Linha 24.
- **Descrição:** O log de erro exibe a exceção diretamente no console, o que pode conter caminhos de sistema ou metadados sensíveis.
- **Evidência:**
  ```python
  except Exception as e:
      print(f"Erro no processamento em background: {e}")
  ```
- **Impacto Potencial:** Information Disclosure que auxilia no mapeamento de ataques.
- **Severidade:** 🟡 Média
- **Recomendação:** Implementar logger estruturado e sanitizado para evitar vazamento de stack traces em produção.
- **Referências:** OWASP A09:2021, CWE-209.

### VULN-006: Política de Senha de Baixa Entropia
- **Localização:** `src/views/auth_view.py`, Função `cadastro`, Linha 57.
- **Descrição:** A validação de senha verifica apenas o comprimento mínimo, ignorando complexidade (caracteres especiais, números, letras).
- **Evidência:** `if len(senha) < 8:`.
- **Impacto Potencial:** Vulnerabilidade a ataques de dicionário e credential stuffing.
- **Severidade:** 🟡 Média
- **Recomendação:** Implementar validação via Regex ou bibliotecas como `zxcvbn`.
- **Referências:** OWASP A07:2021, CWE-521.

### VULN-007: Ausência de Limitação de Taxa (Rate Limiting)
- **Localização:** `src/views/auth_view.py`, Rotas `/login` e `/cadastro`.
- **Descrição:** Não há limites para o número de tentativas de autenticação, permitindo ataques de força bruta offline e online.
- **Evidência:** Ausência de decoradores de limite em rotas críticas.
- **Impacto Potencial:** Comprometimento massivo de contas de usuários.
- **Severidade:** 🟡 Média
- **Recomendação:** Implementar `Flask-Limiter`.
- **Referências:** OWASP A07:2021, CWE-307.

### VULN-008: Configuração de Sessão em Canal Inseguro (HTTPS)
- **Localização:** `src/config.py`.
- **Descrição:** O flag `SESSION_COOKIE_SECURE` está definido como `False`.
- **Evidência:** `SESSION_COOKIE_SECURE = False`.
- **Impacto Potencial:** Envio de cookies de sessão em texto plano em redes Wi-Fi públicas, permitindo interceptação (Sniffing).
- **Severidade:** 🔵 Baixa (Em ambiente de desenvolvimento) / Alta (Em produção).
- **Recomendação:** Alterar para `True` e garantir o uso de TLS/SSL.
- **Referências:** OWASP A02:2021, CWE-614.
