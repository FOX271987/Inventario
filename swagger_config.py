# swagger_config.py - VERSIÓN CON JWT REAL
from flask_restx import Api, fields
from flask import Blueprint, request, jsonify
from functools import wraps
import jwt
import datetime
import os

# Crear blueprint para Swagger
swagger_blueprint = Blueprint('swagger', __name__)

# ===== CONFIGURACIÓN JWT =====
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'tu-clave-secreta-super-segura-12345')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

# ===== FUNCIONES DE JWT =====

def generar_token(user_id, email, nombre, rol):
    """Generar token JWT para el usuario"""
    payload = {
        'user_id': user_id,
        'email': email,
        'nombre': nombre,
        'rol': rol,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.datetime.utcnow()
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token

def verificar_token(token):
    """Verificar y decodificar token JWT"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def obtener_token_desde_header():
    """Extraer token del header Authorization"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
    
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None
    
    return parts[1]

# ===== DECORADORES =====

def token_required(f):
    """Decorador para proteger rutas con JWT"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = obtener_token_desde_header()
        
        if not token:
            return jsonify({'error': 'Token no proporcionado', 'code': 'NO_TOKEN'}), 401
        
        payload = verificar_token(token)
        
        if not payload:
            return jsonify({'error': 'Token inválido o expirado', 'code': 'INVALID_TOKEN'}), 401
        
        request.user = payload
        return f(*args, **kwargs)
    
    return decorated

def admin_required(f):
    """Decorador para rutas que requieren rol admin"""
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if request.user.get('rol') != 'admin':
            return jsonify({'error': 'Acceso denegado'}), 403
        return f(*args, **kwargs)
    return decorated

def editor_required(f):
    """Decorador para rutas que requieren rol editor o admin"""
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        rol = request.user.get('rol')
        if rol not in ['admin', 'editor']:
            return jsonify({'error': 'Acceso denegado'}), 403
        return f(*args, **kwargs)
    return decorated

# ===== CONFIGURACIÓN DE LA API =====

authorizations = {
    'Bearer Auth': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
        'description': 'Ingresa el token JWT con el formato: Bearer &lt;token&gt;'
    }
}

api = Api(
    swagger_blueprint,
    title='Sistema de Seguridad e Inventario API',
    version='1.0',
    description='API REST para gestión de usuarios, autenticación y productos con JWT',
    doc='/docs/',
    authorizations=authorizations,
    security='Bearer Auth'
)

# ===== MODELOS DE SWAGGER =====

# Modelos de Usuario
user_model = api.model('Usuario', {
    'id': fields.Integer(readonly=True, description='ID del usuario'),
    'nombre': fields.String(required=True, description='Nombre completo'),
    'email': fields.String(required=True, description='Email del usuario'),
    'rol': fields.String(required=True, description='Rol del usuario', enum=['admin', 'editor', 'lector'])
})

user_create_model = api.model('UsuarioCrear', {
    'nombre': fields.String(required=True, description='Nombre completo'),
    'email': fields.String(required=True, description='Email del usuario'),
    'password': fields.String(required=True, description='Contraseña (mínimo 6 caracteres)'),
    'rol': fields.String(required=True, description='Rol del usuario', enum=['admin', 'editor', 'lector'])
})

user_update_model = api.model('UsuarioActualizar', {
    'nombre': fields.String(description='Nombre completo'),
    'email': fields.String(description='Email del usuario'),
    'rol': fields.String(description='Rol del usuario', enum=['admin', 'editor', 'lector']),
    'nueva_password': fields.String(description='Nueva contraseña (opcional)')
})

# Modelos de Autenticación
login_model = api.model('Login', {
    'email': fields.String(required=True, description='Email del usuario'),
    'password': fields.String(required=True, description='Contraseña'),
    'ubicacion': fields.Raw(description='Datos de ubicación (opcional)')
})

verification_model = api.model('Verificacion', {
    'email': fields.String(required=True, description='Email del usuario'),
    'codigo': fields.String(required=True, description='Código de verificación de 6 dígitos')
})

password_recovery_model = api.model('RecuperacionPassword', {
    'email': fields.String(required=True, description='Email para recuperación'),
    'codigo': fields.String(required=True, description='Código de verificación'),
    'nueva_password': fields.String(required=True, description='Nueva contraseña'),
    'confirm_password': fields.String(required=True, description='Confirmación de contraseña')
})

# Modelos de Ubicación
location_model = api.model('Ubicacion', {
    'latitud': fields.Float(required=True, description='Latitud'),
    'longitud': fields.Float(required=True, description='Longitud'),
    'precision': fields.Float(description='Precisión en metros'),
    'offline': fields.Boolean(description='Indica si es modo offline')
})

service_model = api.model('Servicio', {
    'nombre': fields.String(description='Nombre del servicio'),
    'tipo': fields.String(description='Tipo de servicio'),
    'distancia': fields.String(description='Distancia desde la ubicación'),
    'direccion': fields.String(description='Dirección del servicio'),
    'lat': fields.Float(description='Latitud'),
    'lng': fields.Float(description='Longitud')
})

# ===== MODELOS DE PRODUCTOS =====

producto_model = api.model('Producto', {
    'ID_Producto': fields.Integer(readonly=True, description='ID del producto'),
    'Codigo': fields.String(required=True, description='Código único del producto'),
    'Nombre': fields.String(required=True, description='Nombre del producto'),
    'Descripcion': fields.String(description='Descripción del producto'),
    'Categoria': fields.String(description='Categoría del producto'),
    'Unidad': fields.String(required=True, description='Unidad de medida'),
    'Stock_Minimo': fields.Integer(description='Stock mínimo', default=0),
    'Stock_Actual': fields.Integer(description='Stock actual', default=0),
    'Activo': fields.Boolean(description='Estado del producto', default=True),
    'Fecha_Creacion': fields.DateTime(description='Fecha de creación')
})

producto_create_model = api.model('ProductoCrear', {
    'Codigo': fields.String(required=True, description='Código único del producto'),
    'Nombre': fields.String(required=True, description='Nombre del producto'),
    'Descripcion': fields.String(description='Descripción del producto'),
    'Categoria': fields.String(description='Categoría del producto'),
    'Unidad': fields.String(required=True, description='Unidad de medida (ej: pz, kg, lt)'),
    'Stock_Minimo': fields.Integer(description='Stock mínimo', default=0),
    'Stock_Actual': fields.Integer(description='Stock inicial', default=0)
})

producto_update_model = api.model('ProductoActualizar', {
    'Codigo': fields.String(description='Código único del producto'),
    'Nombre': fields.String(description='Nombre del producto'),
    'Descripcion': fields.String(description='Descripción del producto'),
    'Categoria': fields.String(description='Categoría del producto'),
    'Unidad': fields.String(description='Unidad de medida'),
    'Stock_Minimo': fields.Integer(description='Stock mínimo'),
    'Stock_Actual': fields.Integer(description='Stock actual')
})

# ===== MODELOS DE MOVIMIENTOS =====

movimiento_entrada_model = api.model('MovimientoEntrada', {
    'ID_Producto': fields.Integer(required=True, description='ID del producto'),
    'Cantidad': fields.Integer(required=True, description='Cantidad a ingresar'),
    'Referencia_Documento': fields.String(description='Número de factura o documento'),
    'Responsable': fields.String(required=True, description='Persona responsable'),
    'ID_Proveedor': fields.Integer(description='ID del proveedor')
})

movimiento_salida_model = api.model('MovimientoSalida', {
    'ID_Producto': fields.Integer(required=True, description='ID del producto'),
    'Cantidad': fields.Integer(required=True, description='Cantidad a retirar'),
    'Referencia_Documento': fields.String(description='Número de orden o documento'),
    'Responsable': fields.String(required=True, description='Persona responsable'),
    'ID_Cliente': fields.Integer(description='ID del cliente')
})

movimiento_model = api.model('Movimiento', {
    'ID_Movimiento': fields.Integer(readonly=True, description='ID del movimiento'),
    'Fecha': fields.DateTime(description='Fecha del movimiento'),
    'Tipo': fields.String(description='Tipo de movimiento', enum=['Entrada', 'Salida']),
    'ID_Producto': fields.Integer(description='ID del producto'),
    'Cantidad': fields.Integer(description='Cantidad'),
    'Referencia_Documento': fields.String(description='Documento de referencia'),
    'Responsable': fields.String(description='Persona responsable')
})