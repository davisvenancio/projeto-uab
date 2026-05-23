from flask import Blueprint, render_template, request, flash, redirect, url_for
from ..models import db, Usuario, OrdemServico
from ..services.auth_service import login_required
from ..services.report_service import calcular_tempo_medio_resolucao, calcular_custo_por_setor, calcular_recorrencias_por_unidade

usuarios_bp = Blueprint("usuarios", __name__)

@usuarios_bp.route("/lideranca")
@login_required(perfis=["admin"])
def lideranca():
    tempo_medio = calcular_tempo_medio_resolucao()
    custo_setor = calcular_custo_por_setor()
    recorrencias = calcular_recorrencias_por_unidade()
    tecnicos = Usuario.query.filter_by(perfil="tecnico").order_by(Usuario.nome).all()

    return render_template("usuarios/lideranca.html",
                           tempo_medio=tempo_medio,
                           custo_setor=custo_setor,
                           recorrencias=recorrencias,
                           tecnicos=tecnicos)

@usuarios_bp.route("/cadastrar-tecnico", methods=["GET", "POST"])
@login_required(perfis=["admin"])
def cadastrar_tecnico():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")

        if not nome or not email or not senha:
            flash("Todos os campos são obrigatórios.")
            return render_template("usuarios/cadastrar_tecnico.html"), 400

        if len(senha) < 8:
            flash("A senha deve ter no mínimo 8 caracteres.")
            return render_template("usuarios/cadastrar_tecnico.html"), 400

        if Usuario.query.filter_by(email=email).first():
            flash("E-mail já cadastrado.")
            return render_template("usuarios/cadastrar_tecnico.html"), 409

        try:
            tecnico = Usuario(nome=nome, email=email, perfil="tecnico")
            tecnico.definir_senha(senha)
            db.session.add(tecnico)
            db.session.commit()
            flash(f"Técnico {nome} cadastrado com sucesso.")
            return redirect(url_for("usuarios.lideranca"))
        except Exception:
            db.session.rollback()
            flash("Erro ao cadastrar técnico.")
            return render_template("usuarios/cadastrar_tecnico.html"), 500

    return render_template("usuarios/cadastrar_tecnico.html")

@usuarios_bp.route("/<int:usuario_id>/excluir-tecnico", methods=["POST"])
@login_required(perfis=["admin"])
def excluir_tecnico(usuario_id):
    tecnico = Usuario.query.filter_by(id=usuario_id, perfil="tecnico").first_or_404()

    chamados_ativos = OrdemServico.query.filter_by(tecnico_id=usuario_id).filter(OrdemServico.status.in_(["pendente", "em_atendimento"])).count()

    if chamados_ativos > 0:
        flash("Não é possível excluir um técnico com chamados em aberto.")
        return redirect(url_for("usuarios.lideranca"))

    try:
        db.session.delete(tecnico)
        db.session.commit()
        flash("Técnico excluído.")
    except Exception:
        db.session.rollback()
        flash("Erro ao excluir técnico.")

    return redirect(url_for("usuarios.lideranca"))
