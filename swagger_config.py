# swagger_config.py - VERSIÓN CON JWT INTEGRADO (Header + Cookie)
from flask_restx import Api, fields
from flask import Blueprint, request, jsonify, session
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

def obtener_token():
    """
    Obtener token JWT de múltiples fuentes (en orden de prioridad):
    1. Header Authorization: Bearer <token>
    2. Cookie jwt_token
    3. Sesión de Flask
    """
    # 1. Intentar desde header Authorization
    auth_header = request.headers.get('Authorization')
    if auth_header:
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == 'bearer':
            return parts[1]
    
    # 2. Intentar desde cookie
    token_cookie = request.cookies.get('jwt_token')
    if token_cookie:
        return token_cookie
    
    # 3. Intentar desde sesión de Flask
    token_session = session.get('jwt_token')
    if token_session:
        return token_session
    
    return None

# ===== DECORADORES =====

def token_required(f):
    """
    Decorador para proteger rutas con JWT.
    Acepta token desde: Header, Cookie, o Sesión de Flask.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = obtener_token()
        
        if not token:
            return {'error': 'Token no proporcionado', 'code': 'NO_TOKEN'}, 401
        
        payload = verificar_token(token)
        
        if not payload:
            return {'error': 'Token inválido o expirado', 'code': 'INVALID_TOKEN'}, 401
        
        # Guardar datos del usuario en request para uso posterior
        request.user = payload
        
        # También actualizar la sesión de Flask para compatibilidad
        session['user_id'] = payload['user_id']
        session['user_email'] = payload['email']
        session['user_nombre'] = payload['nombre']
        session['user_rol'] = payload['rol']
        
        return f(*args, **kwargs)
    
    return decorated

def token_optional(f):
    """
    Decorador que intenta validar JWT pero no falla si no existe.
    Útil para rutas que funcionan con o sin autenticación.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = obtener_token()
        
        if token:
            payload = verificar_token(token)
            if payload:
                request.user = payload
                session['user_id'] = payload['user_id']
                session['user_email'] = payload['email']
                session['user_nombre'] = payload['nombre']
                session['user_rol'] = payload['rol']
            else:
                request.user = None
        else:
            request.user = None
        
        return f(*args, **kwargs)
    
    return decorated

def admin_required(f):
    """Decorador para rutas que requieren rol admin"""
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if request.user.get('rol') != 'admin':
            return {'error': 'Acceso denegado. Se requiere rol de administrador.'}, 403
        return f(*args, **kwargs)
    return decorated

def editor_required(f):
    """Decorador para rutas que requieren rol editor o admin"""
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        rol = request.user.get('rol')
        if rol not in ['admin', 'editor']:
            return {'error': 'Acceso denegado. Se requiere rol de editor o administrador.'}, 403
        return f(*args, **kwargs)
    return decorated

def rol_requerido(*roles_permitidos):
    """
    Decorador flexible para especificar qué roles pueden acceder.
    Uso: @rol_requerido('admin', 'editor')
    """
    def decorator(f):
        @wraps(f)
        @token_required
        def decorated(*args, **kwargs):
            rol = request.user.get('rol')
            if rol not in roles_permitidos:
                return {'error': f'Acceso denegado. Roles permitidos: {", ".join(roles_permitidos)}'}, 403
            return f(*args, **kwargs)
        return decorated
    return decorator

# ===== CONFIGURACIÓN DE LA API =====

authorizations = {
    'Bearer Auth': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
        'description': 'Ingresa el token JWT con el formato: Bearer <token>'
    }
}

api = Api(
    swagger_blueprint,
    title='Sistema de Seguridad e Inventario API',
    version='2.0',
    description='''
    API REST para gestión de usuarios, autenticación y productos con JWT.
    
    **Autenticación:**
    - Hacer login en la web genera automáticamente un JWT
    - El JWT se puede usar desde el header Authorization: Bearer <token>
    - También se acepta JWT desde cookies (para llamadas desde el frontend)
    
    **Roles:**
    - admin: Acceso total
    - editor: Puede crear/editar productos y movimientos
    - lector: Solo puede ver información
    ''',
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
    'password': fields.String(required=True, description='Contraseña')
})

token_response_model = api.model('TokenResponse', {
    'message': fields.String(description='Mensaje de respuesta'),
    'token': fields.String(description='Token JWT'),
    'user': fields.Nested(user_model, description='Datos del usuario')
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

# ===== MODELOS DE PROVEEDORES Y CLIENTES =====

proveedor_model = api.model('Proveedor', {
    'ID_Proveedor': fields.Integer(readonly=True, description='ID del proveedor'),
    'Nombre': fields.String(required=True, description='Nombre del proveedor'),
    'Contacto': fields.String(description='Persona de contacto'),
    'Telefono': fields.String(description='Teléfono'),
    'Email': fields.String(description='Email'),
    'Direccion': fields.String(description='Dirección')
})

cliente_model = api.model('Cliente', {
    'ID_Cliente': fields.Integer(readonly=True, description='ID del cliente'),
    'Nombre': fields.String(required=True, description='Nombre del cliente'),
    'Contacto': fields.String(description='Persona de contacto'),
    'Telefono': fields.String(description='Teléfono'),
    'Email': fields.String(description='Email'),
    'Direccion': fields.String(description='Dirección')
})