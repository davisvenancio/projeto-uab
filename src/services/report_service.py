from sqlalchemy import func, desc
from ..models import db, OrdemServico, Setor, Usuario
from .. import cache

@cache.memoize(timeout=60)
def calcular_tempo_medio_resolucao():
    ordens_concluidas = OrdemServico.query.filter_by(status="concluido").all()

    if not ordens_concluidas:
        return None

    total_segundos = 0
    for ordem in ordens_concluidas:
        delta = ordem.atualizado_em - ordem.criado_em
        total_segundos += delta.total_seconds()

    media_horas = (total_segundos / len(ordens_concluidas)) / 3600
    return round(media_horas, 2)

@cache.memoize(timeout=60)
def calcular_custo_por_setor():
    resultados = (
        db.session.query(
            Setor.nome,
            func.sum(OrdemServico.custo).label("total_custo")
        )
        .join(OrdemServico, OrdemServico.setor_id == Setor.id)
        .filter(OrdemServico.custo.isnot(None))
        .group_by(Setor.nome)
        .all()
    )
    return [{"setor": r.nome, "total_custo": float(r.total_custo)} for r in resultados]

@cache.memoize(timeout=60)
def calcular_recorrencias_por_unidade():
    resultados = (
        db.session.query(
            Usuario.unidade,
            Usuario.bloco,
            func.count(OrdemServico.id).label("total_chamados")
        )
        .join(OrdemServico, OrdemServico.morador_id == Usuario.id)
        .group_by(Usuario.unidade, Usuario.bloco)
        .order_by(desc("total_chamados"))
        .all()
    )
    return [
        {"unidade": r.unidade, "bloco": r.bloco, "total_chamados": r.total_chamados}
        for r in resultados
    ]
