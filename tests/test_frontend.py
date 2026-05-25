import pytest
from src.models import db, Usuario, OrdemServico, Setor

def test_base_template_elements(client):
    """Verifica se elementos base como Bootstrap Icons e CSS customizado estão presentes."""
    response = client.get("/auth/login")
    assert response.status_code == 200
    assert b"bootstrap-icons.min.css" in response.data
    assert b"custom.css" in response.data
    assert b"CondoFix" in response.data
    assert b"bi-tools" in response.data  # Ícone na navbar

def test_login_page_frontend_structure(client):
    """Verifica a estrutura visual da página de login."""
    response = client.get("/auth/login")
    assert b"needs-validation" in response.data
    assert b"bi-shield-lock" in response.data
    assert b"bi-envelope" in response.data
    assert b"bi-key" in response.data

def test_listar_chamados_empty_state(client, app):
    """Verifica o Empty State quando não há chamados."""
    # Login como admin para ver todos
    client.post("/auth/login", data={"email": "admin@condofix.local", "senha": "admin@1234"})
    
    # Limpar chamados se houver (em um ambiente de teste isolado o db deve estar limpo)
    with app.app_context():
        OrdemServico.query.delete()
        db.session.commit()
        
    response = client.get("/chamados/listar")
    assert b"empty-state" in response.data
    assert b"bi-clipboard-x" in response.data
    assert b"Nenhum chamado encontrado" in response.data

def test_detalhes_chamado_frontend_elements(client, app):
    """Verifica elementos visuais na página de detalhes."""
    with app.app_context():
        morador = Usuario(nome="Morador Teste", email="morador_fe@test.com", perfil="morador")
        morador.definir_senha("pass")
        setor = Setor.query.filter_by(nome="Elétrica").first()
        if not setor:
            setor = Setor(nome="Elétrica")
            db.session.add(setor)
        db.session.add(morador)
        db.session.commit()
        os = OrdemServico(
            titulo="Curto Circuito", 
            descricao="Fumaça na tomada", 
            status="pendente",
            morador_id=morador.id,
            setor_id=setor.id
        )
        db.session.add(os)
        db.session.commit()
        os_id = os.id

    client.post("/auth/login", data={"email": "admin@condofix.local", "senha": "admin@1234"})
    response = client.get(f"/chamados/{os_id}/detalhes")
    
    assert b"bi-file-earmark-text" in response.data
    assert b"bi-geo-alt-fill" in response.data
    assert b"bi-person-fill" in response.data
    assert b"bg-warning" in response.data  # Badge de status pendente
    assert b"data-confirm" in response.data  # Atributo de confirmação no botão rejeitar
