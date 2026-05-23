from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime
import enum

db = SQLAlchemy()
bcrypt = Bcrypt()

class PerfilUsuario(enum.Enum):
    MORADOR = "morador"
    TECNICO = "tecnico"
    ADMIN = "admin"

class StatusChamado(enum.Enum):
    PENDENTE = "pendente"
    EM_ATENDIMENTO = "em_atendimento"
    CONCLUIDO = "concluido"
    REJEITADO = "rejeitado"

class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(128), nullable=False)
    perfil = db.Column(db.String(20), nullable=False)
    unidade = db.Column(db.String(20), nullable=True)
    bloco = db.Column(db.String(20), nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    def verificar_senha(self, senha_plain):
        return bcrypt.check_password_hash(self.senha_hash, senha_plain)

    def definir_senha(self, senha_plain):
        self.senha_hash = bcrypt.generate_password_hash(senha_plain).decode('utf-8')

class OrdemServico(db.Model):
    __tablename__ = "ordens_servico"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    titulo = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pendente")
    foto_base64 = db.Column(db.Text, nullable=True)
    parecer_tecnico = db.Column(db.Text, nullable=True)
    custo = db.Column(db.Numeric(10, 2), nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    morador_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    tecnico_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    setor_id = db.Column(db.Integer, db.ForeignKey("setores.id"), nullable=True)

    morador = db.relationship("Usuario", foreign_keys=[morador_id], backref="chamados_abertos")
    tecnico = db.relationship("Usuario", foreign_keys=[tecnico_id], backref="chamados_atendidos")
    setor = db.relationship("Setor", backref="ordens")

class Setor(db.Model):
    __tablename__ = "setores"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(50), nullable=False, unique=True)

def seed_data():
    # Admin
    if not Usuario.query.filter_by(perfil="admin").first():
        admin = Usuario(
            nome="Administrador",
            email="admin@condofix.local",
            perfil="admin"
        )
        admin.definir_senha("admin@1234")
        db.session.add(admin)

    # Técnico padrão
    if not Usuario.query.filter_by(perfil="tecnico").first():
        tecnico = Usuario(
            nome="Técnico de Manutenção",
            email="tecnico@condofix.local",
            perfil="tecnico"
        )
        tecnico.definir_senha("tecnico@1234")
        db.session.add(tecnico)

    # Morador padrão
    if not Usuario.query.filter_by(perfil="morador").first():
        morador = Usuario(
            nome="Maria Moradora",
            email="morador@condofix.local",
            perfil="morador",
            unidade="101",
            bloco="A"
        )
        morador.definir_senha("morador@1234")
        db.session.add(morador)

    # Setores padrão
    setores = ["Elétrica", "Hidráulica", "Civil", "Limpeza", "Elevadores"]
    for nome_setor in setores:
        if not Setor.query.filter_by(nome=nome_setor).first():
            db.session.add(Setor(nome=nome_setor))

    db.session.commit()
