from src.models import Usuario, db

def test_login_sucesso(client):
    # O seed_data já cria o admin
    response = client.post("/auth/login", data={
        "email": "admin@condofix.local",
        "senha": "admin@1234"
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert "Olá, Administrador".encode("utf-8") in response.data

def test_login_falha(client):
    response = client.post("/auth/login", data={
        "email": "admin@condofix.local",
        "senha": "errada"
    })
    
    assert response.status_code == 401
    assert "Credenciais inválidas.".encode("utf-8") in response.data

def test_acesso_negado_morador_em_admin(client, app):
    # Criar morador para o teste
    with app.app_context():
        if not Usuario.query.filter_by(email="morador@test.com").first():
            morador = Usuario(nome="Morador Teste", email="morador@test.com", perfil="morador")
            morador.definir_senha("password123")
            db.session.add(morador)
            db.session.commit()

    # Login como morador
    client.post("/auth/login", data={
        "email": "morador@test.com",
        "senha": "password123"
    })
    
    # Tenta acessar dashboard de admin
    response = client.get("/usuarios/lideranca", follow_redirects=True)
    assert "Acesso não autorizado.".encode("utf-8") in response.data
