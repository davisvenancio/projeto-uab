# Plano de Testes — CondoFix (Senior TDD Suite)

Este documento detalha a estratégia de testes automatizados de alto nível implementada para o sistema CondoFix, focada em robustez, segurança e conformidade arquitetural.

## 1. Estratégia de Testes

- **Abordagem:** Test-Driven Development (TDD) com foco em comportamento (BDD-style assertions).
- **Ferramentas:** `pytest`, `pytest-mock`.
- **Ambiente:** Banco de dados SQLite em memória para isolamento total entre testes.
- **Padrões de Código:** Uso de `db.session.get()` (SQLAlchemy 2.0+) e gestão rigorosa de Application Context.

## 2. Cobertura de Cenários

### 2.1. Autenticação e Segurança (RBAC)
- **Login de Sucesso:** Validação de criação de sessão e persistência de identidade.
- **Falha de Autenticação:** Verificação de tratamento de credenciais inválidas (401).
- **Controle de Acesso (RBAC):** Garante que moradores não acessem rotas administrativas (Painel de Liderança).

### 2.2. Gestão de Chamados e Fluxos (Integração)
- **Criação de Chamado:** Fluxo completo incluindo upload de arquivo (`multipart/form-data`) e validação de persistência.
- **Delegação Administrativa:** Validação da atribuição de técnicos e mudança automática de status para `em_atendimento`.
- **Máquina de Estados:** Bloqueio de transições de status inválidas (ex: Pendente -> Concluído).
- **Restrição Admin (Concluído):** Garante que administradores não possam delegar ou alterar o custo de chamados que já estejam no status `concluido`.

### 2.4. Otimização e Performance
- **Cache de Relatórios:** Validação de que múltiplas chamadas ao dashboard administrativo não resultam em consultas redundantes ao banco (via mock ou timing).
- **Processamento Assíncrono:** Verificação de que o chamado é criado imediatamente enquanto a imagem é processada em segundo plano.

### 2.3. Validações e Limites (Edge Cases)
- **Integridade de Imagem:** Bloqueio de extensões não permitidas (ex: .txt, .pdf).
- **Limite de Payload:** Validação do limite de **2MB** para fotos, conforme constante `MAX_IMAGE_SIZE_BYTES`.

### 2.4. Lógica de Negócio (KPIs)
- **Cálculo de Performance:** Validação da fórmula de tempo médio de resolução, garantindo o isolamento de chamados não concluídos.

### 2.5. Testes de Frontend e Interface (UI/UX)
- **Responsividade:** Validar o layout em resoluções Mobile (375px), Tablet (768px) e Desktop (1200px+). Garantir que o menu colapse e tabelas fiquem responsivas.
- **Acessibilidade:** Validar presença de atributos ARIA, contraste de cores e navegação via teclado.
- **Renderização Condicional:** Verificar se elementos específicos de perfis (ex: botão "Delegar" para Admin) aparecem apenas para os usuários autorizados.
- **Validação de Formulários:** Testar feedbacks visuais de erro (`.is-invalid`) e mensagens de validação em tempo real.
- **Estados de Carregamento e Erro:** Validar exibição de spinners durante submissão e tratamento de estados vazios (Empty States).
- **Integração Frontend/Backend:** Testar o fluxo completo de submissão de formulários via UI, incluindo uploads de imagem.
- **Testes E2E (End-to-End):** Fluxo crítico: Morador abre chamado -> Admin delega -> Técnico conclui -> Sistema calcula KPI.

## 3. Estrutura de Arquivos
- `tests/conftest.py`: Fixtures globais (app, client, db initialization).
- `tests/test_auth.py`: Autenticação e Autorização.
- `tests/test_chamados.py`: Fluxos de OS e Máquina de Estados.
- `tests/test_validation.py`: Validações de entrada e limites de arquivos.
- `tests/test_services.py`: Lógica de serviços e cálculos de dashboard.

## 4. Execução dos Testes

Os testes são executados dentro do ambiente Dockerizado para garantir paridade com a produção:

```bash
docker exec -it condofix-app pytest -v
```

---
**Última Atualização:** 23/05/2026
**Responsável:** David Venancio da Silva Sousa
**Status:** 100% PASS
