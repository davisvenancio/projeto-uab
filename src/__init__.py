from flask import Flask
from .config import Config
from .models import db, bcrypt, seed_data
# Blueprints will be imported here later

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    bcrypt.init_app(app)

    with app.app_context():
        db.create_all()
        seed_data()

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
