from src.services.report_service import calcular_tempo_medio_resolucao
from src.models import db, OrdemServico, Usuario
from datetime import datetime, timedelta

def test_calcular_tempo_medio(app):
    with app.app_context():
        morador = Usuario(nome="M", email="m@test.com", perfil="morador")
        morador.definir_senha("p")
        db.session.add(morador)
        db.session.commit()
        
        # OS concluída em 2 horas
        os1 = OrdemServico(
            titulo="Teste 1", descricao="Desc", status="concluido",
            morador_id=morador.id,
            criado_em=datetime.utcnow() - timedelta(hours=2),
            atualizado_em=datetime.utcnow()
        )
        
        # OS concluída em 4 horas
        os2 = OrdemServico(
            titulo="Teste 2", descricao="Desc", status="concluido",
            morador_id=morador.id,
            criado_em=datetime.utcnow() - timedelta(hours=4),
            atualizado_em=datetime.utcnow()
        )
        
        # OS pendente (não deve entrar no cálculo)
        os3 = OrdemServico(
            titulo="Teste 3", descricao="Desc", status="pendente",
            morador_id=morador.id
        )
        
        db.session.add_all([os1, os2, os3])
        db.session.commit()
        
        media = calcular_tempo_medio_resolucao()
        assert media == 3.0  # (2 + 4) / 2
