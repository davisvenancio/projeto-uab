from flask import Flask
from .config import Config
from .models import db, bcrypt, seed_admin
from flask_caching import Cache
from flask_executor import Executor
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman

cache = Cache()
executor = Executor()
csrf = CSRFProtect()
talisman = Talisman()

def create_app(test_config=None):
    app = Flask(__name__)
    if test_config:
        app.config.from_mapping(test_config)
    else:
        app.config.from_object(Config)

    db.init_app(app)
    bcrypt.init_app(app)
    cache.init_app(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 300})
    executor.init_app(app)
    csrf.init_app(app)
    
    # Enable Talisman for security headers (CSP, HSTS, etc.)
    # In development, we might need to adjust CSP if using external CDNs
    talisman.init_app(app, 
                      content_security_policy=None, # Set to None for now to avoid breaking existing CDNs, but recommend specific CSP later
                      force_https=False) # Keep False for development unless testing HTTPS

    if not app.config.get("TESTING"):
        with app.app_context():
            from . import models
            app.logger.info("Criando tabelas no banco de dados...")
            db.create_all()
            app.logger.info("Tabelas criadas com sucesso.")
            seed_admin()
            app.logger.info("Seed do administrador executado.")

    # Import and register blueprints
    from .views.auth_view import auth_bp
    from .views.chamados_view import chamados_bp
    from .views.usuarios_view import usuarios_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(chamados_bp, url_prefix="/chamados")
    app.register_blueprint(usuarios_bp, url_prefix="/usuarios")

    @app.route("/")
    def index():
        from flask import redirect, url_for
        return redirect(url_for("auth.login"))

    return app
