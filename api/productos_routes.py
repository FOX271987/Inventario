# api/productos_routes.py
from flask import Blueprint, render_template

productos_web_bp = Blueprint('productos_web', __name__, url_prefix='/productos')

@productos_web_bp.route('/')
def lista_productos():
    """Página principal de gestión de productos"""
    return render_template('productos.html')

@productos_web_bp.route('/login')
def login_productos():
    """Página de login con JWT"""
    return render_template('login_jwt.html')