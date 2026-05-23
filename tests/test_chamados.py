import pytest
from io import BytesIO
from src.models import db, OrdemServico, Usuario, Setor
from datetime import datetime

def test_criar_chamado_fluxo_feliz(client):
    # Login como morador
    client.post("/auth/login", data={"email": "morador@condofix.local", "senha": "morador@1234"})
    
    # Simula envio de arquivo
    data = {
        "titulo": "Vazamento Teste",
        "descricao": "Descrição do vazamento",
        "setor_id": "1",
        "foto": (BytesIO(b"dummy image content"), "test.jpg")
    }
    
    response = client.post("/chamados/criar", data=data, content_type="multipart/form-data", follow_redirects=True)
    assert response.status_code == 200
    assert "Chamado aberto com sucesso.".encode("utf-8") in response.data
    
    with client.application.app_context():
        chamado = OrdemServico.query.filter_by(titulo="Vazamento Teste").first()
        assert chamado is not None
        assert chamado.status == "pendente"

def test_transicao_status_invalida(client):
    # Login como tecnico
    client.post("/auth/login", data={"email": "tecnico@condofix.local", "senha": "tecnico@1234"})
    
    with client.application.app_context():
        morador = Usuario.query.filter_by(perfil="morador").first()
        tecnico = Usuario.query.filter_by(perfil="tecnico").first()
        os = OrdemServico(
            titulo="OS Transição", descricao="Desc", status="pendente",
            morador_id=morador.id, tecnico_id=tecnico.id
        )
        db.session.add(os)
        db.session.commit()
        os_id = os.id

    # Tenta concluir sem passar por "em_atendimento"
    response = client.post(f"/chamados/{os_id}/atualizar-status", data={
        "status": "concluido",
        "parecer_tecnico": "Tentativa inválida"
    }, follow_redirects=True)
    
    assert "Transição de status inválida.".encode("utf-8") in response.data
    
    with client.application.app_context():
        os_pos = db.session.get(OrdemServico, os_id)
        assert os_pos.status == "pendente"

def test_delegar_chamado_admin(client):
    client.post("/auth/login", data={"email": "admin@condofix.local", "senha": "admin@1234"})
    
    with client.application.app_context():
        morador = Usuario.query.filter_by(perfil="morador").first()
        tecnico = Usuario.query.filter_by(perfil="tecnico").first()
        os = OrdemServico(titulo="Delegar", descricao="Desc", status="pendente", morador_id=morador.id)
        db.session.add(os)
        db.session.commit()
        os_id = os.id
        tecnico_id = tecnico.id

    response = client.post(f"/chamados/{os_id}/delegar", data={"tecnico_id": str(tecnico_id)}, follow_redirects=True)
    assert "delegado para".encode("utf-8") in response.data.lower()
    
    with client.application.app_context():
        os_pos = db.session.get(OrdemServico, os_id)
        assert os_pos.status == "em_atendimento"
        assert os_pos.tecnico_id == tecnico_id
