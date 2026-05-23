# Especificação Técnica do Sistema — CondoFix

> **Disciplina:** Análise e Desenvolvimento de Sistemas / Engenharia de Software
> **Stack:** Python 3, Flask, Jinja2, Bootstrap 5, SQLite, Docker

---

## Convenções Gerais

- Toda função retorna explicitamente o objeto de resposta Flask ou executa `redirect()`.
- Todas as operações de escrita no banco são encerradas com `db.session.commit()` em caso de sucesso ou `db.session.rollback()` em caso de exceção.
- Senhas são sempre armazenadas como hash `bcrypt`. Nunca em texto plano.
- Imagens são sempre armazenadas como string Base64 no campo `TEXT` do banco.
- O controle de acesso é feito pelo decorador `@login_required(perfil=...)` definido em `auth_service.py`.

---

## `run.py`

- **Ação:** criar
- **Descrição:** Ponto de entrada da aplicação. Inicializa a factory da aplicação Flask e executa o servidor de desenvolvimento.

```
PSEUDOCÓDIGO run.py:

  IMPORTAR create_app DE src

  app = create_app()

  SE __name__ == "__main__":
    app.run()
```

---

## `src/__init__.py`

- **Ação:** criar
- **Descrição:** Factory function da aplicação Flask. Registra extensões (SQLAlchemy), carrega configurações, cria as tabelas do banco de dados, executa o seed do administrador inicial e registra todos os Blueprints de rotas.

```
PSEUDOCÓDIGO src/__init__.py:

  FUNÇÃO create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    COM app.app_context():
      db.create_all()
      seed_admin()  // Inserir admin padrão se não existir

    app.register_blueprint(auth_bp,      url_prefix="/auth")
    app.register_blueprint(chamados_bp,  url_prefix="/chamados")
    app.register_blueprint(usuarios_bp,  url_prefix="/usuarios")

    RETORNAR app
```

---

## `src/config.py`

- **Ação:** criar
- **Descrição:** Lê todas as variáveis de ambiente e as expõe como atributos de uma classe `Config` consumida pela factory.

```
PSEUDOCÓDIGO src/config.py:

  CLASSE Config:
    SECRET_KEY     = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG          = os.environ.get("FLASK_DEBUG") == "1"
    MAX_IMAGE_SIZE_BYTES = 2 * 1024 * 1024   // 2 MB
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
```

---

## `src/models.py`

- **Ação:** criar
- **Descrição:** Define todas as entidades mapeadas pelo ORM Flask-SQLAlchemy. Inclui o enum de papéis (`perfil`) e status de chamado (`status`), além da função de seed do administrador padrão.

### Enum `PerfilUsuario`

```
ENUM PerfilUsuario:
  MORADOR    = "morador"
  TECNICO    = "tecnico"
  ADMIN      = "admin"
```

### Enum `StatusChamado`

```
ENUM StatusChamado:
  PENDENTE      = "pendente"
  EM_ATENDIMENTO = "em_atendimento"
  CONCLUIDO     = "concluido"
  REJEITADO     = "rejeitado"
```

### Model `Usuario` → tabela `usuarios`

```
PSEUDOCÓDIGO Model Usuario:

  id           : INTEGER, PRIMARY KEY, AUTOINCREMENT
  nome         : TEXT, NOT NULL
  email        : TEXT, NOT NULL, UNIQUE
  senha_hash   : TEXT, NOT NULL
  perfil       : TEXT, NOT NULL  // ENUM PerfilUsuario
  unidade      : TEXT, NULLABLE  // Somente moradores
  bloco        : TEXT, NULLABLE  // Somente moradores
  criado_em    : DATETIME, DEFAULT = agora()

  MÉTODO verificar_senha(senha_plain):
    RETORNAR bcrypt.check_password_hash(self.senha_hash, senha_plain)

  MÉTODO definir_senha(senha_plain):
    self.senha_hash = bcrypt.generate_password_hash(senha_plain)
```

### Model `OrdemServico` → tabela `ordens_servico`

```
PSEUDOCÓDIGO Model OrdemServico:

  id            : INTEGER, PRIMARY KEY, AUTOINCREMENT
  titulo        : TEXT, NOT NULL
  descricao     : TEXT, NOT NULL
  status        : TEXT, NOT NULL, DEFAULT = "pendente"  // ENUM StatusChamado
  foto_base64   : TEXT, NULLABLE
  parecer_tecnico : TEXT, NULLABLE
  custo         : NUMERIC(10,2), NULLABLE
  criado_em     : DATETIME, DEFAULT = agora()
  atualizado_em : DATETIME, DEFAULT = agora(), ON UPDATE = agora()

  // Chaves estrangeiras
  morador_id    : INTEGER, FK → usuarios.id, NOT NULL
  tecnico_id    : INTEGER, FK → usuarios.id, NULLABLE
  setor_id      : INTEGER, FK → setores.id, NULLABLE
```

### Model `Setor` → tabela `setores`

```
PSEUDOCÓDIGO Model Setor:

  id   : INTEGER, PRIMARY KEY, AUTOINCREMENT
  nome : TEXT, NOT NULL, UNIQUE
```

### Função `seed_admin()`

```
PSEUDOCÓDIGO seed_admin():

  SE Usuario.query.filter_by(perfil="admin").first() É NULO:
    admin = Usuario(
      nome       = "Administrador",
      email      = "admin@condofix.local",
      perfil     = PerfilUsuario.ADMIN
    )
    admin.definir_senha("admin@1234")
    db.session.add(admin)
    db.session.commit()
```

---

## `src/services/auth_service.py`

- **Ação:** criar
- **Descrição:** Encapsula a lógica de autenticação, controle de sessão Flask e o decorador `@login_required`. O decorador intercepta qualquer requisição, verifica a sessão ativa e o perfil autorizado, e redireciona para o login em caso de falha.

```
PSEUDOCÓDIGO auth_service.py:

  FUNÇÃO login_required(perfis=[]):
    // Decorador de ordem superior
    RETORNAR decorador que:
      VERIFICA SE "usuario_id" EXISTE em flask.session
        SE NÃO:
          flash("Sessão expirada. Faça login.")
          REDIRECIONAR para "/auth/login"

      usuario = Usuario.query.get(session["usuario_id"])

      SE usuario É NULO:
        session.clear()
        REDIRECIONAR para "/auth/login"

      SE perfis NÃO ESTÁ VAZIO E usuario.perfil NÃO ESTÁ EM perfis:
        flash("Acesso não autorizado.")
        REDIRECIONAR para "/auth/login"

      INJETAR usuario em flask.g.usuario_atual
      EXECUTAR função original


  FUNÇÃO autenticar(email, senha_plain):
    usuario = Usuario.query.filter_by(email=email).first()

    SE usuario É NULO OU usuario.verificar_senha(senha_plain) É FALSO:
      RETORNAR None

    RETORNAR usuario


  FUNÇÃO iniciar_sessao(usuario):
    session.clear()
    session["usuario_id"] = usuario.id
    session["usuario_perfil"] = usuario.perfil
    session["usuario_nome"] = usuario.nome


  FUNÇÃO encerrar_sessao():
    session.clear()
```

---

## `src/services/image_service.py`

- **Ação:** criar
- **Descrição:** Processa o arquivo de imagem recebido do formulário multipart. Valida extensão e tamanho máximo (2 MB). Converte o binário em string Base64 pronta para armazenamento no banco e renderização direta em `<img src="data:image/...">`.

```
PSEUDOCÓDIGO image_service.py:

  CONSTANTE ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
  CONSTANTE MAX_SIZE_BYTES      = 2 * 1024 * 1024

  FUNÇÃO processar_imagem(arquivo_form):
    // arquivo_form = objeto FileStorage do Flask

    SE arquivo_form É NULO OU arquivo_form.filename É VAZIO:
      RETORNAR None

    extensao = arquivo_form.filename.split(".")[-1].lower()

    SE extensao NÃO ESTÁ EM ALLOWED_EXTENSIONS:
      LANÇAR ValueError("Extensão não permitida. Use: jpg, jpeg, png ou webp.")

    conteudo_bytes = arquivo_form.read()

    SE len(conteudo_bytes) > MAX_SIZE_BYTES:
      LANÇAR ValueError("Imagem excede o limite de 2 MB.")

    base64_str = base64.b64encode(conteudo_bytes).decode("utf-8")
    mime_type  = f"image/{extensao}"

    RETORNAR f"data:{mime_type};base64,{base64_str}"
```

---

## `src/services/report_service.py`

- **Ação:** criar
- **Descrição:** Executa agregações sobre a tabela `ordens_servico` para gerar os indicadores do painel administrativo: tempo médio de resolução (em horas), custo total por setor e contagem de recorrências por unidade.

```
PSEUDOCÓDIGO report_service.py:

  FUNÇÃO calcular_tempo_medio_resolucao():
    // Retorna float em horas ou None se não houver dados
    ordens_concluidas = OrdemServico.query.filter_by(status="concluido").all()

    SE ordens_concluidas ESTÁ VAZIO:
      RETORNAR None

    total_segundos = 0
    PARA CADA ordem EM ordens_concluidas:
      delta = ordem.atualizado_em - ordem.criado_em
      total_segundos += delta.total_seconds()

    media_horas = (total_segundos / len(ordens_concluidas)) / 3600
    RETORNAR round(media_horas, 2)


  FUNÇÃO calcular_custo_por_setor():
    // Retorna lista de dicionários [{setor_nome, total_custo}]
    resultados = (
      db.session.query(
        Setor.nome,
        db.func.sum(OrdemServico.custo).label("total_custo")
      )
      .join(OrdemServico, OrdemServico.setor_id == Setor.id)
      .filter(OrdemServico.custo NÃO É NULO)
      .group_by(Setor.nome)
      .all()
    )
    RETORNAR [{"setor": r.nome, "total_custo": r.total_custo} PARA r EM resultados]


  FUNÇÃO calcular_recorrencias_por_unidade():
    // Retorna lista [{unidade, bloco, total_chamados}] ordenada decrescente
    resultados = (
      db.session.query(
        Usuario.unidade,
        Usuario.bloco,
        db.func.count(OrdemServico.id).label("total_chamados")
      )
      .join(OrdemServico, OrdemServico.morador_id == Usuario.id)
      .group_by(Usuario.unidade, Usuario.bloco)
      .order_by(db.desc("total_chamados"))
      .all()
    )
    RETORNAR [
      {"unidade": r.unidade, "bloco": r.bloco, "total_chamados": r.total_chamados}
      PARA r EM resultados
    ]
```

---

## `src/views/auth_view.py`

- **Ação:** criar
- **Descrição:** Blueprint `auth_bp` responsável pelas rotas de autenticação: exibição e processamento do formulário de login, autocadastro público de moradores e logout.

---

### `GET /auth/login` — Exibir formulário de login

```
PSEUDOCÓDIGO GET /auth/login:

  SE "usuario_id" EXISTE em session:
    REDIRECIONAR para rota adequada conforme perfil (ver lógica de redirecionamento pós-login)

  RENDERIZAR template "auth/login.html"
```

---

### `POST /auth/login` — Processar login

```
PSEUDOCÓDIGO POST /auth/login:

  email       = request.form.get("email", "").strip().lower()
  senha_plain = request.form.get("senha", "")

  SE email ESTÁ VAZIO OU senha_plain ESTÁ VAZIO:
    flash("E-mail e senha são obrigatórios.")
    RENDERIZAR "auth/login.html", status=400

  usuario = autenticar(email, senha_plain)

  SE usuario É NULO:
    flash("Credenciais inválidas.")
    RENDERIZAR "auth/login.html", status=401

  iniciar_sessao(usuario)

  SE usuario.perfil == "morador":
    REDIRECIONAR para "/chamados/meus-pedidos"
  SE usuario.perfil == "tecnico":
    REDIRECIONAR para "/chamados/fila"
  SE usuario.perfil == "admin":
    REDIRECIONAR para "/chamados/listar"
```

---

### `GET /auth/cadastro` — Exibir formulário de autocadastro (moradores)

```
PSEUDOCÓDIGO GET /auth/cadastro:

  RENDERIZAR template "auth/cadastro.html"
```

---

### `POST /auth/cadastro` — Processar autocadastro de morador

```
PSEUDOCÓDIGO POST /auth/cadastro:

  nome    = request.form.get("nome", "").strip()
  email   = request.form.get("email", "").strip().lower()
  senha   = request.form.get("senha", "")
  unidade = request.form.get("unidade", "").strip()
  bloco   = request.form.get("bloco", "").strip()

  SE nome ESTÁ VAZIO OU email ESTÁ VAZIO OU senha ESTÁ VAZIO OU unidade ESTÁ VAZIO:
    flash("Todos os campos obrigatórios devem ser preenchidos.")
    RENDERIZAR "auth/cadastro.html", status=400

  SE len(senha) < 8:
    flash("A senha deve ter no mínimo 8 caracteres.")
    RENDERIZAR "auth/cadastro.html", status=400

  SE Usuario.query.filter_by(email=email).first() NÃO É NULO:
    flash("E-mail já cadastrado.")
    RENDERIZAR "auth/cadastro.html", status=409

  TENTAR:
    novo_usuario = Usuario(nome=nome, email=email, perfil="morador", unidade=unidade, bloco=bloco)
    novo_usuario.definir_senha(senha)
    db.session.add(novo_usuario)
    db.session.commit()
    flash("Conta criada com sucesso! Faça login.")
    REDIRECIONAR para "/auth/login"
  EXCETO:
    db.session.rollback()
    flash("Erro interno. Tente novamente.")
    RENDERIZAR "auth/cadastro.html", status=500
```

---

### `GET /auth/logout` — Encerrar sessão

```
PSEUDOCÓDIGO GET /auth/logout:

  encerrar_sessao()
  flash("Sessão encerrada.")
  REDIRECIONAR para "/auth/login"
```

---

## `src/views/chamados_view.py`

- **Ação:** criar
- **Descrição:** Blueprint `chamados_bp` responsável pelas rotas de gerenciamento das ordens de serviço. O acesso a cada rota é controlado por `@login_required` com o perfil correspondente.

---

### `GET /chamados/criar` — Exibir formulário de abertura de chamado (morador)

```
PSEUDOCÓDIGO GET /chamados/criar:

  @login_required(perfis=["morador"])

  setores = Setor.query.order_by(Setor.nome).all()
  RENDERIZAR "chamados/criar.html", setores=setores
```

---

### `POST /chamados/criar` — Processar abertura de chamado (morador)

```
PSEUDOCÓDIGO POST /chamados/criar:

  @login_required(perfis=["morador"])

  titulo    = request.form.get("titulo", "").strip()
  descricao = request.form.get("descricao", "").strip()
  setor_id  = request.form.get("setor_id")
  arquivo   = request.files.get("foto")

  SE titulo ESTÁ VAZIO OU descricao ESTÁ VAZIO:
    flash("Título e descrição são obrigatórios.")
    REDIRECIONAR para "GET /chamados/criar"

  foto_base64 = None
  SE arquivo EXISTE E arquivo.filename NÃO ESTÁ VAZIO:
    TENTAR:
      foto_base64 = processar_imagem(arquivo)
    EXCETO ValueError como erro:
      flash(str(erro))
      REDIRECIONAR para "GET /chamados/criar"

  TENTAR:
    nova_os = OrdemServico(
      titulo      = titulo,
      descricao   = descricao,
      status      = "pendente",
      foto_base64 = foto_base64,
      morador_id  = g.usuario_atual.id,
      setor_id    = setor_id SE setor_id NÃO ESTÁ VAZIO SENÃO None
    )
    db.session.add(nova_os)
    db.session.commit()
    flash("Chamado aberto com sucesso.")
    REDIRECIONAR para "/chamados/meus-pedidos"
  EXCETO:
    db.session.rollback()
    flash("Erro ao salvar o chamado.")
    REDIRECIONAR para "GET /chamados/criar"
```

---

### `GET /chamados/meus-pedidos` — Listar chamados do morador autenticado

```
PSEUDOCÓDIGO GET /chamados/meus-pedidos:

  @login_required(perfis=["morador"])

  chamados = OrdemServico.query
    .filter_by(morador_id=g.usuario_atual.id)
    .order_by(OrdemServico.criado_em.desc())
    .all()

  RENDERIZAR "chamados/listar.html", chamados=chamados, titulo="Meus Pedidos"
```

---

### `GET /chamados/fila` — Listar chamados delegados ao técnico autenticado

```
PSEUDOCÓDIGO GET /chamados/fila:

  @login_required(perfis=["tecnico"])

  chamados = OrdemServico.query
    .filter_by(tecnico_id=g.usuario_atual.id)
    .filter(OrdemServico.status.in_(["pendente", "em_atendimento"]))
    .order_by(OrdemServico.criado_em.asc())
    .all()

  RENDERIZAR "chamados/listar.html", chamados=chamados, titulo="Minha Fila"
```

---

### `GET /chamados/listar` — Listar todos os chamados (admin)

```
PSEUDOCÓDIGO GET /chamados/listar:

  @login_required(perfis=["admin"])

  status_filtro  = request.args.get("status")
  tecnico_filtro = request.args.get("tecnico_id")

  query = OrdemServico.query

  SE status_filtro NÃO ESTÁ VAZIO:
    query = query.filter_by(status=status_filtro)

  SE tecnico_filtro NÃO ESTÁ VAZIO:
    query = query.filter_by(tecnico_id=int(tecnico_filtro))

  chamados = query.order_by(OrdemServico.criado_em.desc()).all()
  tecnicos = Usuario.query.filter_by(perfil="tecnico").all()

  RENDERIZAR "chamados/listar.html",
    chamados=chamados,
    tecnicos=tecnicos,
    titulo="Todos os Chamados"
```

---

### `GET /chamados/<int:chamado_id>/detalhes` — Exibir detalhes de um chamado

```
PSEUDOCÓDIGO GET /chamados/<chamado_id>/detalhes:

  @login_required(perfis=["morador", "tecnico", "admin"])

  os = OrdemServico.query.get_or_404(chamado_id)

  // Moradores só podem ver seus próprios chamados
  SE g.usuario_atual.perfil == "morador" E os.morador_id != g.usuario_atual.id:
    flash("Acesso negado.")
    REDIRECIONAR para "/chamados/meus-pedidos"

  // Técnicos só podem ver chamados delegados a eles
  SE g.usuario_atual.perfil == "tecnico" E os.tecnico_id != g.usuario_atual.id:
    flash("Acesso negado.")
    REDIRECIONAR para "/chamados/fila"

  RENDERIZAR "chamados/detalhes.html", os=os
```

---

### `POST /chamados/<int:chamado_id>/atualizar-status` — Técnico atualiza status e parecer

```
PSEUDOCÓDIGO POST /chamados/<chamado_id>/atualizar-status:

  @login_required(perfis=["tecnico"])

  os = OrdemServico.query.get_or_404(chamado_id)

  SE os.tecnico_id != g.usuario_atual.id:
    flash("Você não tem permissão para atualizar este chamado.")
    REDIRECIONAR para "/chamados/fila"

  novo_status     = request.form.get("status")
  parecer_tecnico = request.form.get("parecer_tecnico", "").strip()

  TRANSICOES_VALIDAS = {
    "pendente":       ["em_atendimento"],
    "em_atendimento": ["concluido"]
  }

  SE novo_status NÃO ESTÁ EM TRANSICOES_VALIDAS.get(os.status, []):
    flash("Transição de status inválida.")
    REDIRECIONAR para "/chamados/<chamado_id>/detalhes"

  SE novo_status == "concluido" E parecer_tecnico ESTÁ VAZIO:
    flash("O parecer técnico é obrigatório para concluir o chamado.")
    REDIRECIONAR para "/chamados/<chamado_id>/detalhes"

  TENTAR:
    os.status          = novo_status
    os.parecer_tecnico = parecer_tecnico SE parecer_tecnico NÃO ESTÁ VAZIO SENÃO os.parecer_tecnico
    os.atualizado_em   = agora()
    db.session.commit()
    flash("Status atualizado.")
  EXCETO:
    db.session.rollback()
    flash("Erro ao atualizar o chamado.")

  REDIRECIONAR para "/chamados/<chamado_id>/detalhes"
```

---

### `POST /chamados/<int:chamado_id>/delegar` — Admin delega chamado a um técnico

```
PSEUDOCÓDIGO POST /chamados/<chamado_id>/delegar:

  @login_required(perfis=["admin"])

  os        = OrdemServico.query.get_or_404(chamado_id)
  tecnico_id = int(request.form.get("tecnico_id"))

  tecnico = Usuario.query.filter_by(id=tecnico_id, perfil="tecnico").first()

  SE tecnico É NULO:
    flash("Técnico inválido.")
    REDIRECIONAR para "/chamados/<chamado_id>/detalhes"

  TENTAR:
    os.tecnico_id  = tecnico_id
    os.status      = "em_atendimento"
    os.atualizado_em = agora()
    db.session.commit()
    flash(f"Chamado delegado para {tecnico.nome}.")
  EXCETO:
    db.session.rollback()
    flash("Erro ao delegar o chamado.")

  REDIRECIONAR para "/chamados/<chamado_id>/detalhes"
```

---

### `POST /chamados/<int:chamado_id>/rejeitar` — Admin rejeita um chamado

```
PSEUDOCÓDIGO POST /chamados/<chamado_id>/rejeitar:

  @login_required(perfis=["admin"])

  os = OrdemServico.query.get_or_404(chamado_id)

  SE os.status != "pendente":
    flash("Somente chamados pendentes podem ser rejeitados.")
    REDIRECIONAR para "/chamados/<chamado_id>/detalhes"

  TENTAR:
    os.status      = "rejeitado"
    os.atualizado_em = agora()
    db.session.commit()
    flash("Chamado rejeitado.")
  EXCETO:
    db.session.rollback()
    flash("Erro ao rejeitar o chamado.")

  REDIRECIONAR para "/chamados/listar"
```

---

### `POST /chamados/<int:chamado_id>/custo` — Admin registra custo da OS

```
PSEUDOCÓDIGO POST /chamados/<chamado_id>/custo:

  @login_required(perfis=["admin"])

  os = OrdemServico.query.get_or_404(chamado_id)

  SE os.status == "concluido":
    flash("Não é possível alterar o custo de um chamado já concluído.")
    REDIRECIONAR para "/chamados/<chamado_id>/detalhes"

  custo = request.form.get("custo", "").strip()

  TENTAR:
    custo_decimal = Decimal(custo)
    SE custo_decimal < 0:
      LANÇAR ValueError
  EXCETO:
    flash("Custo inválido. Informe um valor numérico positivo.")
    REDIRECIONAR para "/chamados/<chamado_id>/detalhes"

  TENTAR:
    os.custo = custo_decimal
    db.session.commit()
    flash("Custo registrado.")
  EXCETO:
    db.session.rollback()
    flash("Erro ao registrar custo.")

  REDIRECIONAR para "/chamados/<chamado_id>/detalhes"
```

---

## `src/views/usuarios_view.py`

- **Ação:** criar
- **Descrição:** Blueprint `usuarios_bp` responsável pelas rotas de gestão de usuários. Inclui o painel de liderança (admin), o cadastro de técnicos e o CRUD completo de técnicos (exclusão e edição).

---

### `GET /usuarios/lideranca` — Painel administrativo e relatórios (admin)

```
PSEUDOCÓDIGO GET /usuarios/lideranca:

  @login_required(perfis=["admin"])

  tempo_medio  = calcular_tempo_medio_resolucao()
  custo_setor  = calcular_custo_por_setor()
  recorrencias = calcular_recorrencias_por_unidade()
  tecnicos     = Usuario.query.filter_by(perfil="tecnico").order_by(Usuario.nome).all()

  RENDERIZAR "usuarios/lideranca.html",
    tempo_medio  = tempo_medio,
    custo_setor  = custo_setor,
    recorrencias = recorrencias,
    tecnicos     = tecnicos
```

---

### `GET /usuarios/cadastrar-tecnico` — Exibir formulário de cadastro de técnico (admin)

```
PSEUDOCÓDIGO GET /usuarios/cadastrar-tecnico:

  @login_required(perfis=["admin"])

  RENDERIZAR "usuarios/cadastrar_tecnico.html"
```

---

### `POST /usuarios/cadastrar-tecnico` — Processar cadastro de técnico (admin)

```
PSEUDOCÓDIGO POST /usuarios/cadastrar-tecnico:

  @login_required(perfis=["admin"])

  nome  = request.form.get("nome", "").strip()
  email = request.form.get("email", "").strip().lower()
  senha = request.form.get("senha", "")

  SE nome ESTÁ VAZIO OU email ESTÁ VAZIO OU senha ESTÁ VAZIO:
    flash("Todos os campos são obrigatórios.")
    RENDERIZAR "usuarios/cadastrar_tecnico.html", status=400

  SE len(senha) < 8:
    flash("A senha deve ter no mínimo 8 caracteres.")
    RENDERIZAR "usuarios/cadastrar_tecnico.html", status=400

  SE Usuario.query.filter_by(email=email).first() NÃO É NULO:
    flash("E-mail já cadastrado.")
    RENDERIZAR "usuarios/cadastrar_tecnico.html", status=409

  TENTAR:
    tecnico = Usuario(nome=nome, email=email, perfil="tecnico")
    tecnico.definir_senha(senha)
    db.session.add(tecnico)
    db.session.commit()
    flash(f"Técnico {nome} cadastrado com sucesso.")
    REDIRECIONAR para "/usuarios/lideranca"
  EXCETO:
    db.session.rollback()
    flash("Erro ao cadastrar técnico.")
    RENDERIZAR "usuarios/cadastrar_tecnico.html", status=500
```

---

### `POST /usuarios/<int:usuario_id>/excluir-tecnico` — Excluir técnico (admin)

```
PSEUDOCÓDIGO POST /usuarios/<usuario_id>/excluir-tecnico:

  @login_required(perfis=["admin"])

  tecnico = Usuario.query.filter_by(id=usuario_id, perfil="tecnico").first_or_404()

  chamados_ativos = OrdemServico.query
    .filter_by(tecnico_id=usuario_id)
    .filter(OrdemServico.status.in_(["pendente", "em_atendimento"]))
    .count()

  SE chamados_ativos > 0:
    flash("Não é possível excluir um técnico com chamados em aberto.")
    REDIRECIONAR para "/usuarios/lideranca"

  TENTAR:
    db.session.delete(tecnico)
    db.session.commit()
    flash("Técnico excluído.")
  EXCETO:
    db.session.rollback()
    flash("Erro ao excluir técnico.")

  REDIRECIONAR para "/usuarios/lideranca"
```

---

## `src/templates/base.html`

- **Ação:** criar
- **Descrição:** Template Jinja2 base que define a estrutura HTML comum a todas as páginas: `<head>` com Bootstrap 5, navbar responsiva com links condicionais por perfil de sessão, área de mensagens flash e bloco `{% block content %}` a ser sobrescrito pelos templates filhos.

```
PSEUDOCÓDIGO base.html (estrutura de blocos Jinja2):

  <!DOCTYPE html>
  <html lang="pt-BR">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}CondoFix{% endblock %}</title>
    <link rel="stylesheet" href="[Bootstrap 5 CDN]">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/custom.css') }}">
  </head>
  <body>
    <nav>
      SE session.usuario_perfil == "morador":
        EXIBIR link "Meus Pedidos" → /chamados/meus-pedidos
        EXIBIR link "Abrir Chamado" → /chamados/criar
      SE session.usuario_perfil == "tecnico":
        EXIBIR link "Minha Fila" → /chamados/fila
      SE session.usuario_perfil == "admin":
        EXIBIR link "Chamados" → /chamados/listar
        EXIBIR link "Painel" → /usuarios/lideranca
        EXIBIR link "Novo Técnico" → /usuarios/cadastrar-tecnico
      SE session.usuario_id EXISTE:
        EXIBIR link "Sair" → /auth/logout
      SENÃO:
        EXIBIR link "Login" → /auth/login
    </nav>

    // Mensagens flash
    PARA CADA mensagem EM get_flashed_messages():
      RENDERIZAR alerta Bootstrap

    <main>
      {% block content %}{% endblock %}
    </main>

    <script src="[Bootstrap 5 JS CDN]"></script>
    <script src="{{ url_for('static', filename='js/main.js') }}"></script>
  </body>
  </html>
```

---

## `src/templates/auth/login.html`

- **Ação:** criar
- **Descrição:** Formulário de login com campos `email` e `senha`. Exibe link para `/auth/cadastro`. Método `POST` para `/auth/login`.

---

## `src/templates/auth/cadastro.html`

- **Ação:** criar
- **Descrição:** Formulário de autocadastro para moradores com campos: `nome`, `email`, `senha`, `unidade` e `bloco`. Método `POST` para `/auth/cadastro`.

---

## `src/templates/chamados/criar.html`

- **Ação:** criar
- **Descrição:** Formulário de abertura de OS para moradores. Campos: `titulo`, `descricao`, `setor_id` (select populado via Jinja2), `foto` (input tipo `file`, `enctype="multipart/form-data"`). Método `POST` para `/chamados/criar`.

---

## `src/templates/chamados/listar.html`

- **Ação:** criar
- **Descrição:** Template reutilizável para listagem de chamados. Recebe via contexto Jinja2: `chamados` (lista de OS), `titulo` (string), e opcionalmente `tecnicos` (lista de usuários técnicos para filtro admin). Exibe tabela Bootstrap com colunas: ID, Título, Status (badge colorido), Setor, Morador, Técnico, Data. Links para detalhes de cada OS.

---

## `src/templates/chamados/detalhes.html`

- **Ação:** criar
- **Descrição:** Exibe todos os campos da OS. Condicionalmente renderiza:
  - **Morador:** somente visualização.
  - **Técnico:** formulário de atualização de status (`POST /chamados/<id>/atualizar-status`) com campo `parecer_tecnico`.
  - **Admin:** formulários de delegação (`POST /chamados/<id>/delegar`), rejeição (`POST /chamados/<id>/rejeitar`) e registro de custo (`POST /chamados/<id>/custo`). Se `foto_base64` existir, renderiza `<img src="{{ os.foto_base64 }}">`.

---

## `src/templates/usuarios/lideranca.html`

- **Ação:** criar
- **Descrição:** Painel administrativo. Exibe: cards de KPI com `tempo_medio`, tabela de `custo_setor`, tabela de `recorrencias`. Lista de técnicos com botão de exclusão (`POST /usuarios/<id>/excluir-tecnico`) e link para cadastro de novo técnico.

---

## `src/templates/usuarios/cadastrar_tecnico.html`

- **Ação:** criar
- **Descrição:** Formulário de cadastro de técnico com campos `nome`, `email` e `senha`. Método `POST` para `/usuarios/cadastrar-tecnico`. Visível apenas para admin.

---

## `Dockerfile`

- **Ação:** criar
- **Descrição:** Define a imagem Docker baseada em `python:3.10-slim`. Copia o projeto, instala as dependências de `requirements.txt`, expõe a porta 5000 e define o comando de inicialização.

```
PSEUDOCÓDIGO Dockerfile:

  FROM python:3.10-slim
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt
  COPY . .
  EXPOSE 5000
  ENV FLASK_APP=run.py
  CMD ["flask", "run", "--host=0.0.0.0"]
```

---

## `docker-compose.yml`

- **Ação:** criar
- **Descrição:** Orquestra o contêiner da aplicação. Mapeia a porta 5000, injeta as variáveis de ambiente do arquivo `.env` e monta um volume para persistência do banco SQLite.

```
PSEUDOCÓDIGO docker-compose.yml:

  services:
    web:
      build: .
      ports:
        - "5000:5000"
      env_file:
        - .env
      volumes:
        - ./instance:/app/instance  // Persiste o arquivo .db fora do contêiner
```

---

## `requirements.txt`

- **Ação:** criar
- **Descrição:** Lista todas as dependências Python do projeto com versões fixadas para garantir reprodutibilidade.

```
Flask==3.0.3
Flask-SQLAlchemy==3.1.1
Flask-Bcrypt==1.0.1
python-dotenv==1.0.1
```

---

## `.gitignore`

- **Ação:** criar
- **Descrição:** Exclui do controle de versão arquivos sensíveis e gerados pelo ambiente de desenvolvimento.

```
CONTEÚDO .gitignore:

  .env
  __pycache__/
  *.pyc
  instance/
  .venv/
  *.db
```
