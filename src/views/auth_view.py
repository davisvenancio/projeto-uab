from flask import Blueprint, render_template, request, flash, redirect, url_for, session, current_app
from ..models import Usuario, db
from ..services.auth_service import autenticar, iniciar_sessao, encerrar_sessao

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "usuario_id" in session:
        perfil = session.get("usuario_perfil")
        if perfil == "morador":
            return redirect(url_for("chamados.meus_pedidos"))
        elif perfil == "tecnico":
            return redirect(url_for("chamados.fila"))
        elif perfil == "admin":
            return redirect(url_for("chamados.listar"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha_plain = request.form.get("senha", "")

        if not email or not senha_plain:
            flash("E-mail e senha são obrigatórios.")
            return render_template("auth/login.html"), 400

        usuario = autenticar(email, senha_plain)

        if not usuario:
            flash("Credenciais inválidas.")
            return render_template("auth/login.html"), 401

        iniciar_sessao(usuario)

        if usuario.perfil == "morador":
            return redirect(url_for("chamados.meus_pedidos"))
        elif usuario.perfil == "tecnico":
            return redirect(url_for("chamados.fila"))
        elif usuario.perfil == "admin":
            return redirect(url_for("chamados.listar"))

    return render_template("auth/login.html")

@auth_bp.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        unidade = request.form.get("unidade", "").strip()
        bloco = request.form.get("bloco", "").strip()

        if not nome or not email or not senha or not unidade:
            flash("Todos os campos obrigatórios devem ser preenchidos.")
            return render_template("auth/cadastro.html"), 400

        if len(senha) < 8:
            flash("A senha deve ter no mínimo 8 caracteres.")
            return render_template("auth/cadastro.html"), 400

        if Usuario.query.filter_by(email=email).first():
            # Generic message to avoid user enumeration
            current_app.logger.warning(f"Tentativa de cadastro com e-mail já existente: {email}")
            flash("Não foi possível concluir o cadastro. Verifique os dados ou tente outro e-mail.")
            return render_template("auth/cadastro.html"), 400

        try:
            novo_usuario = Usuario(nome=nome, email=email, perfil="morador", unidade=unidade, bloco=bloco)
            novo_usuario.definir_senha(senha)
            db.session.add(novo_usuario)
            db.session.commit()
            flash("Conta criada com sucesso! Faça login.")
            return redirect(url_for("auth.login"))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao cadastrar usuário: {str(e)}")
            flash("Erro interno no servidor. Tente novamente mais tarde.")
            return render_template("auth/cadastro.html"), 500

    return render_template("auth/cadastro.html")

@auth_bp.route("/logout")
def logout():
    encerrar_sessao()
    flash("Sessão encerrada.")
    return redirect(url_for("auth.login"))
