import pytest
from src.models import db, OrdemServico, Usuario

def test_admin_cannot_delegate_concluded_ticket(client, app):
    # Setup data
    with app.app_context():
        morador = Usuario(nome="Morador", email="morador_r@test.com", perfil="morador")
        morador.definir_senha("p")
        tecnico = Usuario(nome="Tecnico", email="tecnico_r@test.com", perfil="tecnico")
        tecnico.definir_senha("p")
        db.session.add_all([morador, tecnico])
        db.session.commit()
        
        os = OrdemServico(
            titulo="Chamado Concluido", 
            descricao="Desc", 
            status="concluido", 
            morador_id=morador.id,
            tecnico_id=tecnico.id
        )
        db.session.add(os)
        db.session.commit()
        os_id = os.id
        tecnico_id = tecnico.id

    # Login como admin
    client.post("/auth/login", data={"email": "admin@condofix.local", "senha": "admin@1234"})

    # Tenta delegar novamente
    response = client.post(f"/chamados/{os_id}/delegar", data={"tecnico_id": str(tecnico_id)}, follow_redirects=True)
    
    assert "Não é possível delegar um chamado já concluído.".encode("utf-8") in response.data
    
    with client.application.app_context():
        os_pos = db.session.get(OrdemServico, os_id)
        assert os_pos.status == "concluido"

def test_admin_cannot_update_cost_of_concluded_ticket(client, app):
    # Setup data
    with app.app_context():
        morador = Usuario(nome="Morador", email="morador_c@test.com", perfil="morador")
        morador.definir_senha("p")
        db.session.add(morador)
        db.session.commit()
        
        os = OrdemServico(
            titulo="Chamado Concluido Custo", 
            descricao="Desc", 
            status="concluido", 
            morador_id=morador.id,
            custo=100.00
        )
        db.session.add(os)
        db.session.commit()
        os_id = os.id

    # Login como admin
    client.post("/auth/login", data={"email": "admin@condofix.local", "senha": "admin@1234"})

    # Tenta alterar o custo
    response = client.post(f"/chamados/{os_id}/custo", data={"custo": "200.00"}, follow_redirects=True)
    
    assert "Não é possível alterar o custo de um chamado já concluído.".encode("utf-8") in response.data
    
    with client.application.app_context():
        os_pos = db.session.get(OrdemServico, os_id)
        assert os_pos.custo == 100.00
