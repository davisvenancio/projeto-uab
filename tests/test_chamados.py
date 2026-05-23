import pytest
from io import BytesIO
from src.models import db, OrdemServico, Usuario, Setor
from datetime import datetime

def test_criar_chamado_fluxo_feliz(client, app):
    # Criar morador e setor para o teste
    with app.app_context():
        if not Usuario.query.filter_by(email="morador@test.com").first():
            morador = Usuario(nome="Morador Teste", email="morador@test.com", perfil="morador")
            morador.definir_senha("password123")
            db.session.add(morador)
        if not Setor.query.filter_by(id=1).first():
            db.session.add(Setor(id=1, nome="Geral"))
        db.session.commit()

    # Login como morador
    client.post("/auth/login", data={"email": "morador@test.com", "senha": "password123"})
    
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

def test_transicao_status_invalida(client, app):
    # Setup users
    with app.app_context():
        morador = Usuario(nome="M", email="m@test.com", perfil="morador")
        morador.definir_senha("p")
        tecnico = Usuario(nome="T", email="t@test.com", perfil="tecnico")
        tecnico.definir_senha("p")
        db.session.add_all([morador, tecnico])
        db.session.commit()
        
        os = OrdemServico(
            titulo="OS Transição", descricao="Desc", status="pendente",
            morador_id=morador.id, tecnico_id=tecnico.id
        )
        db.session.add(os)
        db.session.commit()
        os_id = os.id

    # Login como tecnico
    client.post("/auth/login", data={"email": "t@test.com", "senha": "p"})

    # Tenta concluir sem passar por "em_atendimento"
    response = client.post(f"/chamados/{os_id}/atualizar-status", data={
        "status": "concluido",
        "parecer_tecnico": "Tentativa inválida"
    }, follow_redirects=True)
    
    assert "Transição de status inválida.".encode("utf-8") in response.data
    
    with client.application.app_context():
        os_pos = db.session.get(OrdemServico, os_id)
        assert os_pos.status == "pendente"

def test_delegar_chamado_admin(client, app):
    # Setup data
    with app.app_context():
        morador = Usuario(nome="M", email="m2@test.com", perfil="morador")
        morador.definir_senha("p")
        tecnico = Usuario(nome="T", email="t2@test.com", perfil="tecnico")
        tecnico.definir_senha("p")
        db.session.add_all([morador, tecnico])
        db.session.commit()
        
        os = OrdemServico(titulo="Delegar", descricao="Desc", status="pendente", morador_id=morador.id)
        db.session.add(os)
        db.session.commit()
        os_id = os.id
        tecnico_id = tecnico.id

    # Login como admin (já semeado no conftest)
    client.post("/auth/login", data={"email": "admin@condofix.local", "senha": "admin@1234"})

    response = client.post(f"/chamados/{os_id}/delegar", data={"tecnico_id": str(tecnico_id)}, follow_redirects=True)
    assert "delegado para".encode("utf-8") in response.data.lower()
    
    with client.application.app_context():
        os_pos = db.session.get(OrdemServico, os_id)
        assert os_pos.status == "em_atendimento"
        assert os_pos.tecnico_id == tecnico_id
