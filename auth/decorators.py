# auth/decorators.py - VERSIÓN CON JWT INTEGRADO
from functools import wraps
from flask import session, redirect, url_for, flash, request, jsonify
import jwt
import os

# Configuración JWT (debe coincidir con swagger_config.py)
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'tu-clave-secreta-super-segura-12345')
JWT_ALGORITHM = 'HS256'

def verificar_token_jwt(token):
    """Verificar y decodificar token JWT"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def obtener_token_de_request():
    """
    Obtener token JWT de múltiples fuentes:
    1. Header Authorization: Bearer <token>
    2. Cookie jwt_token
    3. Sesión de Flask
    """
    # 1. Header Authorization
    auth_header = request.headers.get('Authorization')
    if auth_header:
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == 'bearer':
            return parts[1]
    
    # 2. Cookie
    token_cookie = request.cookies.get('jwt_token')
    if token_cookie:
        return token_cookie
    
    # 3. Sesión de Flask
    token_session = session.get('jwt_token')
    if token_session:
        return token_session
    
    return None

def obtener_usuario_actual():
    """
    Obtener datos del usuario actual desde JWT o sesión.
    Retorna dict con user_id, email, nombre, rol o None.
    """
    # Primero intentar con JWT
    token = obtener_token_de_request()
    if token:
        payload = verificar_token_jwt(token)
        if payload:
            return {
                'user_id': payload.get('user_id'),
                'email': payload.get('email'),
                'nombre': payload.get('nombre'),
                'rol': payload.get('rol')
            }
    
    # Si no hay JWT válido, intentar con sesión de Flask
    if 'user_id' in session:
        return {
            'user_id': session.get('user_id'),
            'email': session.get('user_email'),
            'nombre': session.get('user_nombre'),
            'rol': session.get('user_rol')
        }
    
    return None

def es_request_api():
    """Determinar si la petición es para API (JSON) o para web (HTML)"""
    # Si acepta JSON o viene de Swagger
    if request.is_json:
        return True
    if request.headers.get('Accept', '').find('application/json') != -1:
        return True
    if request.headers.get('Authorization'):
        return True
    if request.path.startswith('/api/'):
        return True
    return False

def login_required(f):
    """
    Decorador que requiere autenticación.
    Funciona con JWT (API) y sesión de Flask (Web).
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        usuario = obtener_usuario_actual()
        
        if not usuario:
            if es_request_api():
                return jsonify({
                    'error': 'Autenticación requerida',
                    'code': 'AUTH_REQUIRED'
                }), 401
            else:
                flash('Debes iniciar sesión para acceder a esta página', 'error')
                return redirect(url_for('auth.login'))
        
        # Guardar usuario en request para uso posterior
        request.current_user = usuario
        
        return f(*args, **kwargs)
    return decorated_function

def twofa_required(f):
    """
    Decorador que requiere verificación 2FA completada.
    Para JWT, se asume que si el token es válido, el 2FA ya pasó.
    Para sesión, verifica twofa_verified.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Si hay JWT válido, el 2FA ya se completó (el token se genera después del 2FA)
        token = obtener_token_de_request()
        if token:
            payload = verificar_token_jwt(token)
            if payload:
                request.current_user = {
                    'user_id': payload.get('user_id'),
                    'email': payload.get('email'),
                    'nombre': payload.get('nombre'),
                    'rol': payload.get('rol')
                }
                return f(*args, **kwargs)
        
        # Si no hay JWT, verificar sesión de Flask
        if 'user_id' not in session:
            if es_request_api():
                return jsonify({
                    'error': 'Autenticación requerida',
                    'code': 'AUTH_REQUIRED'
                }), 401
            else:
                flash('Debes iniciar sesión para acceder a esta página', 'error')
                return redirect(url_for('auth.login'))
        
        if not session.get('twofa_verified', False):
            if es_request_api():
                return jsonify({
                    'error': 'Verificación 2FA requerida',
                    'code': '2FA_REQUIRED'
                }), 401
            else:
                flash('Debes completar la verificación de dos factores', 'warning')
                return redirect(url_for('auth.verificar_2fa'))
        
        request.current_user = {
            'user_id': session.get('user_id'),
            'email': session.get('user_email'),
            'nombre': session.get('user_nombre'),
            'rol': session.get('user_rol')
        }
        
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorador que requiere rol de administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        usuario = obtener_usuario_actual()
        
        if not usuario:
            if es_request_api():
                return jsonify({
                    'error': 'Autenticación requerida',
                    'code': 'AUTH_REQUIRED'
                }), 401
            else:
                flash('Debes iniciar sesión para acceder a esta página', 'error')
                return redirect(url_for('auth.login'))
        
        if usuario.get('rol') != 'admin':
            if es_request_api():
                return jsonify({
                    'error': 'Acceso denegado. Se requiere rol de administrador.',
                    'code': 'ADMIN_REQUIRED'
                }), 403
            else:
                flash('No tienes permisos de administrador para acceder a esta página', 'error')
                return redirect(url_for('users.listar_usuarios'))
        
        request.current_user = usuario
        return f(*args, **kwargs)
    return decorated_function

def editor_required(f):
    """Decorador que requiere rol de editor o administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        usuario = obtener_usuario_actual()
        
        if not usuario:
            if es_request_api():
                return jsonify({
                    'error': 'Autenticación requerida',
                    'code': 'AUTH_REQUIRED'
                }), 401
            else:
                flash('Debes iniciar sesión para acceder a esta página', 'error')
                return redirect(url_for('auth.login'))
        
        if usuario.get('rol') not in ['admin', 'editor']:
            if es_request_api():
                return jsonify({
                    'error': 'Acceso denegado. Se requiere rol de editor o administrador.',
                    'code': 'EDITOR_REQUIRED'
                }), 403
            else:
                flash('No tienes permisos de editor para realizar esta acción', 'error')
                return redirect(url_for('users.listar_usuarios'))
        
        request.current_user = usuario
        return f(*args, **kwargs)
    return decorated_function

def rol_requerido(*roles_permitidos):
    """
    Decorador flexible para especificar qué roles pueden acceder.
    Uso: @rol_requerido('admin', 'editor')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            usuario = obtener_usuario_actual()
            
            if not usuario:
                if es_request_api():
                    return jsonify({
                        'error': 'Autenticación requerida',
                        'code': 'AUTH_REQUIRED'
                    }), 401
                else:
                    flash('Debes iniciar sesión para acceder a esta página', 'error')
                    return redirect(url_for('auth.login'))
            
            if usuario.get('rol') not in roles_permitidos:
                if es_request_api():
                    return jsonify({
                        'error': f'Acceso denegado. Roles permitidos: {", ".join(roles_permitidos)}',
                        'code': 'INSUFFICIENT_ROLE'
                    }), 403
                else:
                    flash(f'No tienes permisos para acceder. Roles requeridos: {", ".join(roles_permitidos)}', 'error')
                    return redirect(url_for('users.listar_usuarios'))
            
            request.current_user = usuario
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ===== DECORADOR PARA API PURA (solo JWT) =====

def jwt_required(f):
    """
    Decorador estricto que SOLO acepta JWT (no sesión de Flask).
    Útil para endpoints de API que no deben usar cookies.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = obtener_token_de_request()
        
        if not token:
            return jsonify({
                'error': 'Token JWT requerido',
                'code': 'NO_TOKEN'
            }), 401
        
        payload = verificar_token_jwt(token)
        
        if not payload:
            return jsonify({
                'error': 'Token inválido o expirado',
                'code': 'INVALID_TOKEN'
            }), 401
        
        request.current_user = {
            'user_id': payload.get('user_id'),
            'email': payload.get('email'),
            'nombre': payload.get('nombre'),
            'rol': payload.get('rol')
        }
        
        return f(*args, **kwargs)
    return decorated_function