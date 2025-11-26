from flask import Flask, redirect, url_for, session
import os
from dotenv import load_dotenv
from flask_cors import CORS
from authlib.integrations.flask_client import OAuth
from utils.notifications import NotificacionesInventario

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'clave-secreta-temporal-12345')

# Configuración de la base de datos
from models import db
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///seguridad.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Configurar CORS
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5000", "http://127.0.0.1:5000"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# ============================================
# ✅ SOLO IMPORTAR api (NO swagger_blueprint)
# ============================================
from swagger_config import api
# ============================================

# Configuración de OAuth
oauth = OAuth(app)

# Configuración de Google OAuth
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID', ''),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET', ''),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile',
        'verify': True,
        'timeout': 30
    }
)

# Importar y registrar blueprints
from auth.routes import auth_bp
from api.users import users_bp
from api.location import location_bp
from api.auth import api_auth_bp
from api.inventory import inventory_bp
from config.swagger_spec import swagger_bp
from api.productos_routes import productos_web_bp

# ============================================
# ✅ IMPORTAR RUTAS DE SWAGGER DESPUÉS
# ============================================
import swagger_routes  # Esto registra las rutas en el api object
# ============================================

app.register_blueprint(auth_bp)
app.register_blueprint(users_bp)
app.register_blueprint(location_bp)
app.register_blueprint(api_auth_bp, url_prefix='/api')
app.register_blueprint(inventory_bp, url_prefix='/api/inventario')
app.register_blueprint(swagger_bp)  # ← Este es de config/swagger_spec.py
app.register_blueprint(productos_web_bp)

# Ruta principal
@app.route('/')
def index():
    return redirect(url_for('auth.login'))

# Inicializar la aplicación
if __name__ == '__main__':
    with app.app_context():
        from utils.database import init_db
        init_db()
        print("✅ Base de datos inicializada")
    
    print("=== Servidor iniciado ===")
    print("URL: http://localhost:5000/login")
    print("Swagger UI: http://localhost:5000/api/docs/")
    print("Productos JWT: http://localhost:5000/productos/login")
    app.run(debug=True, host='0.0.0.0', port=5000)