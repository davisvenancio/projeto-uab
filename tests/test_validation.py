import pytest
from src.services.image_service import processar_imagem
from io import BytesIO

def test_validacao_extensao_imagem(app):
    file = BytesIO(b"fake data")
    file.filename = "test.txt"
    
    with app.app_context():
        with pytest.raises(ValueError) as excinfo:
            processar_imagem(file)
        assert "Extensão não permitida".encode("utf-8") in str(excinfo.value).encode("utf-8")

def test_validacao_tamanho_imagem(app):
    # Simula arquivo maior que 2MB
    large_data = b"0" * (2 * 1024 * 1024 + 1)
    file = BytesIO(large_data)
    file.filename = "test.png"
    
    with app.app_context():
        with pytest.raises(ValueError) as excinfo:
            processar_imagem(file)
        assert "Imagem excede o limite".encode("utf-8") in str(excinfo.value).encode("utf-8")
