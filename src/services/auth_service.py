from functools import wraps
from flask import session, flash, redirect, url_for, g
from ..models import Usuario, db

def login_required(perfis_permitidos=None):
    if perfis_permitidos is None:
        perfis_permitidos = []
        
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "usuario_id" not in session:
                flash("Sessão expirada. Faça login.")
                return redirect(url_for("auth.login"))

            usuario = Usuario.query.get(session["usuario_id"])

            if not usuario:
                session.clear()
                return redirect(url_for("auth.login"))

            if perfis_permitidos and usuario.perfil not in perfis_permitidos:
                flash("Acesso não autorizado.")
                # Redirect to a safe page based on profile
                if usuario.perfil == "morador":
                    return redirect(url_for("chamados.meus_pedidos"))
                elif usuario.perfil == "tecnico":
                    return redirect(url_for("chamados.fila"))
                elif usuario.perfil == "admin":
                    return redirect(url_for("chamados.listar"))
                return redirect(url_for("auth.login"))

            g.usuario_atual = usuario
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def autenticar(email, senha_plain):
    usuario = Usuario.query.filter_by(email=email).first()
    if not usuario or not usuario.verificar_senha(senha_plain):
        return None
    return usuario

def iniciar_sessao(usuario):
    session.clear()
    session["usuario_id"] = usuario.id
    session["usuario_perfil"] = usuario.perfil
    session["usuario_nome"] = usuario.nome

def encerrar_sessao():
    session.clear()
