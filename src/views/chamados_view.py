from flask import Blueprint, render_template, request, flash, redirect, url_for, g
from ..models import db, OrdemServico, Setor, Usuario
from ..services.auth_service import login_required
from ..services.image_service import processar_imagem
from datetime import datetime
from decimal import Decimal

chamados_bp = Blueprint("chamados", __name__)

@chamados_bp.route("/criar", methods=["GET", "POST"])
@login_required(perfis_permitidos=["morador"])
def criar():
    if request.method == "POST":
        titulo = request.form.get("titulo", "").strip()
        descricao = request.form.get("descricao", "").strip()
        setor_id = request.form.get("setor_id")
        arquivo = request.files.get("foto")

        if not titulo or not descricao:
            flash("Título e descrição são obrigatórios.")
            return redirect(url_for("chamados.criar"))

        foto_base64 = None
        if arquivo and arquivo.filename:
            try:
                foto_base64 = processar_imagem(arquivo)
            except ValueError as e:
                flash(str(e))
                return redirect(url_for("chamados.criar"))

        try:
            nova_os = OrdemServico(
                titulo=titulo,
                descricao=descricao,
                status="pendente",
                foto_base64=foto_base64,
                morador_id=g.usuario_atual.id,
                setor_id=int(setor_id) if setor_id else None
            )
            db.session.add(nova_os)
            db.session.commit()
            flash("Chamado aberto com sucesso.")
            return redirect(url_for("chamados.meus_pedidos"))
        except Exception:
            db.session.rollback()
            flash("Erro ao salvar o chamado.")
            return redirect(url_for("chamados.criar"))

    setores = Setor.query.order_by(Setor.nome).all()
    return render_template("chamados/criar.html", setores=setores)

@chamados_bp.route("/meus-pedidos")
@login_required(perfis_permitidos=["morador"])
def meus_pedidos():
    chamados = OrdemServico.query.filter_by(morador_id=g.usuario_atual.id).order_by(OrdemServico.criado_em.desc()).all()
    return render_template("chamados/listar.html", chamados=chamados, titulo="Meus Pedidos")

@chamados_bp.route("/fila")
@login_required(perfis_permitidos=["tecnico"])
def fila():
    chamados = OrdemServico.query.filter_by(tecnico_id=g.usuario_atual.id).filter(OrdemServico.status.in_(["pendente", "em_atendimento"])).order_by(OrdemServico.criado_em.asc()).all()
    return render_template("chamados/listar.html", chamados=chamados, titulo="Minha Fila")

@chamados_bp.route("/listar")
@login_required(perfis_permitidos=["admin"])
def listar():
    status_filtro = request.args.get("status")
    tecnico_filtro = request.args.get("tecnico_id")

    query = OrdemServico.query

    if status_filtro:
        query = query.filter_by(status=status_filtro)
    if tecnico_filtro:
        query = query.filter_by(tecnico_id=int(tecnico_filtro))

    chamados = query.order_by(OrdemServico.criado_em.desc()).all()
    tecnicos = Usuario.query.filter_by(perfil="tecnico").all()
    return render_template("chamados/listar.html", chamados=chamados, tecnicos=tecnicos, titulo="Todos os Chamados")

@chamados_bp.route("/<int:chamado_id>/detalhes")
@login_required(perfis_permitidos=["morador", "tecnico", "admin"])
def detalhes(chamado_id):
    os = OrdemServico.query.get_or_404(chamado_id)

    if g.usuario_atual.perfil == "morador" and os.morador_id != g.usuario_atual.id:
        flash("Acesso negado.")
        return redirect(url_for("chamados.meus_pedidos"))

    if g.usuario_atual.perfil == "tecnico" and os.tecnico_id != g.usuario_atual.id:
        flash("Acesso negado.")
        return redirect(url_for("chamados.fila"))

    return render_template("chamados/detalhes.html", os=os)

@chamados_bp.route("/<int:chamado_id>/atualizar-status", methods=["POST"])
@login_required(perfis_permitidos=["tecnico"])
def atualizar_status(chamado_id):
    os = OrdemServico.query.get_or_404(chamado_id)

    if os.tecnico_id != g.usuario_atual.id:
        flash("Você não tem permissão para atualizar este chamado.")
        return redirect(url_for("chamados.fila"))

    novo_status = request.form.get("status")
    parecer_tecnico = request.form.get("parecer_tecnico", "").strip()

    transicoes_validas = {
        "pendente": ["em_atendimento"],
        "em_atendimento": ["concluido"]
    }

    if novo_status not in transicoes_validas.get(os.status, []):
        flash("Transição de status inválida.")
        return redirect(url_for("chamados.detalhes", chamado_id=chamado_id))

    if novo_status == "concluido" and not parecer_tecnico:
        flash("O parecer técnico é obrigatório para concluir o chamado.")
        return redirect(url_for("chamados.detalhes", chamado_id=chamado_id))

    try:
        os.status = novo_status
        if parecer_tecnico:
            os.parecer_tecnico = parecer_tecnico
        os.atualizado_em = datetime.utcnow()
        db.session.commit()
        flash("Status atualizado.")
    except Exception:
        db.session.rollback()
        flash("Erro ao atualizar o chamado.")

    return redirect(url_for("chamados.detalhes", chamado_id=chamado_id))

@chamados_bp.route("/<int:chamado_id>/delegar", methods=["POST"])
@login_required(perfis_permitidos=["admin"])
def delegar(chamado_id):
    os = OrdemServico.query.get_or_404(chamado_id)
    tecnico_id_raw = request.form.get("tecnico_id")
    
    if not tecnico_id_raw:
        flash("Selecione um técnico.")
        return redirect(url_for("chamados.detalhes", chamado_id=chamado_id))
        
    tecnico_id = int(tecnico_id_raw)
    tecnico = Usuario.query.filter_by(id=tecnico_id, perfil="tecnico").first()

    if not tecnico:
        flash("Técnico inválido.")
        return redirect(url_for("chamados.detalhes", chamado_id=chamado_id))

    try:
        os.tecnico_id = tecnico_id
        os.status = "em_atendimento"
        os.atualizado_em = datetime.utcnow()
        db.session.commit()
        flash(f"Chamado delegado para {tecnico.nome}.")
    except Exception:
        db.session.rollback()
        flash("Erro ao delegar o chamado.")

    return redirect(url_for("chamados.detalhes", chamado_id=chamado_id))

@chamados_bp.route("/<int:chamado_id>/rejeitar", methods=["POST"])
@login_required(perfis_permitidos=["admin"])
def rejeitar(chamado_id):
    os = OrdemServico.query.get_or_404(chamado_id)

    if os.status != "pendente":
        flash("Somente chamados pendentes podem ser rejeitados.")
        return redirect(url_for("chamados.detalhes", chamado_id=chamado_id))

    try:
        os.status = "rejeitado"
        os.atualizado_em = datetime.utcnow()
        db.session.commit()
        flash("Chamado rejeitado.")
    except Exception:
        db.session.rollback()
        flash("Erro ao rejeitar o chamado.")

    return redirect(url_for("chamados.listar"))

@chamados_bp.route("/<int:chamado_id>/custo", methods=["POST"])
@login_required(perfis_permitidos=["admin"])
def registrar_custo(chamado_id):
    os = OrdemServico.query.get_or_404(chamado_id)
    custo_raw = request.form.get("custo", "").strip()

    try:
        custo_decimal = Decimal(custo_raw)
        if custo_decimal < 0:
            raise ValueError
    except (ValueError, Exception):
        flash("Custo inválido. Informe um valor numérico positivo.")
        return redirect(url_for("chamados.detalhes", chamado_id=chamado_id))

    try:
        os.custo = custo_decimal
        db.session.commit()
        flash("Custo registrado.")
    except Exception:
        db.session.rollback()
        flash("Erro ao registrar custo.")

    return redirect(url_for("chamados.detalhes", chamado_id=chamado_id))
