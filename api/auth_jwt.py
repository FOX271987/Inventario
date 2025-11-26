from flask import Blueprint, request, jsonify
from functools import wraps
import jwt
import os
from datetime import datetime, timedelta
from models.user import Usuario
from utils.validation import validar_email, validar_password
from auth.utils import generar_codigo_verificacion, enviar_correo, verificar_conexion
from utils.database import get_connection

auth_jwt_bp = Blueprint('auth_jwt', __name__)

# ===== DECORADOR JWT =====
def jwt_required(f):
    """Decorador para proteger rutas con JWT"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Token mal formado'}), 401
        
        if not token:
            return jsonify({'error': 'Token faltante'}), 401
        
        try:
            # Decodificar token
            data = jwt.decode(
                token, 
                os.getenv('SECRET_KEY', 'clave-secreta-temporal-12345'),
                algorithms=["HS256"]
            )
            current_user_email = data['sub']
            current_user = Usuario.obtener_por_email(current_user_email)
            
            if not current_user:
                return jsonify({'error': 'Usuario no encontrado'}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token inválido'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

# ===== ENDPOINT DE LOGIN JWT =====
@auth_jwt_bp.route('/jwt/login', methods=['POST'])
def jwt_login():
    """Login que retorna JWT token (sin 2FA para React)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'detail': 'Datos JSON requeridos'}), 400
        
        # Soportar tanto 'email' como 'username'
        email = data.get('email') or data.get('username')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'detail': 'Email/Usuario y contraseña son requeridos'}), 400
        
        # Validar email si parece ser un email
        if '@' in email and not validar_email(email):
            return jsonify({'detail': 'Formato de email inválido'}), 400
        
        # Verificar credenciales
        usuario = Usuario.verificar_login(email, password)
        if not usuario:
            return jsonify({'detail': 'Credenciales incorrectas'}), 401
        
        # Generar JWT token
        token_payload = {
            'sub': usuario.email,
            'user_id': usuario.id,
            'nombre': usuario.nombre,
            'rol': usuario.rol,
            'exp': datetime.utcnow() + timedelta(hours=24),  # Token válido 24 horas
            'iat': datetime.utcnow()
        }
        
        token = jwt.encode(
            token_payload,
            os.getenv('SECRET_KEY', 'clave-secreta-temporal-12345'),
            algorithm='HS256'
        )
        
        # Actualizar sesión activa en BD
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE usuarios 
            SET sesion_activa = TRUE, ultima_sesion = CURRENT_TIMESTAMP 
            WHERE id = %s
        """, (usuario.id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'access_token': token,
            'token_type': 'bearer',
            'user': {
                'id': usuario.id,
                'username': usuario.nombre,
                'email': usuario.email,
                'rol': usuario.rol
            }
        }), 200
        
    except Exception as e:
        print(f"❌ Error en jwt_login: {str(e)}")
        return jsonify({'detail': f'Error en el servidor: {str(e)}'}), 500

# ===== ENDPOINT DE LOGIN CON 2FA (Compatible con tu sistema actual) =====
@auth_jwt_bp.route('/jwt/login-2fa', methods=['POST'])
def jwt_login_2fa():
    """Login con 2FA que retorna JWT token después de verificación"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'detail': 'Datos JSON requeridos'}), 400
        
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'detail': 'Email y contraseña son requeridos'}), 400
        
        if not validar_email(email):
            return jsonify({'detail': 'Formato de email inválido'}), 400
        
        # Verificar si ya tiene sesión activa
        from auth.utils import usuario_tiene_sesion_activa
        sesion_activa = usuario_tiene_sesion_activa(email)
        
        if sesion_activa:
            return jsonify({
                'detail': 'Este correo ya tiene una sesión activa en otro dispositivo'
            }), 403
        
        # Verificar credenciales
        usuario = Usuario.verificar_login(email, password)
        if not usuario:
            return jsonify({'detail': 'Credenciales incorrectas'}), 401
        
        # Generar código 2FA
        codigo_verificacion = generar_codigo_verificacion()
        exito_guardado = Usuario.guardar_codigo_verificacion(email, codigo_verificacion)
        
        if not exito_guardado:
            return jsonify({'detail': 'Error al generar código de verificación'}), 500
        
        tiene_conexion = verificar_conexion()
        
        response_data = {
            'success': True,
            'message': 'Código de verificación generado',
            'requires_2fa': True,
            'email': email
        }
        
        # Enviar código por correo
        if tiene_conexion:
            asunto = "Código de verificación - Sistema de Seguridad"
            cuerpo = f"Hola {usuario.nombre}, tu código de verificación es: {codigo_verificacion}"
            
            if enviar_correo(email, asunto, cuerpo):
                response_data['message'] = 'Código de verificación enviado por correo'
            else:
                response_data['codigo_offline'] = codigo_verificacion
                response_data['message'] = 'Error al enviar correo, use el código offline'
        else:
            response_data['codigo_offline'] = codigo_verificacion
            response_data['message'] = 'Modo offline: use el código proporcionado'
        
        return jsonify(response_data), 200
        
    except Exception as e:
        print(f"❌ Error en jwt_login_2fa: {str(e)}")
        return jsonify({'detail': f'Error en el servidor: {str(e)}'}), 500

# ===== VERIFICAR CÓDIGO 2FA Y RETORNAR JWT =====
@auth_jwt_bp.route('/jwt/verify-2fa', methods=['POST'])
def jwt_verify_2fa():
    """Verificar código 2FA y retornar JWT token"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'detail': 'Datos JSON requeridos'}), 400
        
        email = data.get('email')
        codigo = data.get('codigo')
        
        if not email or not codigo:
            return jsonify({'detail': 'Email y código son requeridos'}), 400
        
        # Verificar código
        if not Usuario.verificar_codigo(email, codigo):
            return jsonify({'detail': 'Código de verificación inválido o expirado'}), 401
        
        usuario = Usuario.obtener_por_email(email)
        if not usuario:
            return jsonify({'detail': 'Usuario no encontrado'}), 404
        
        # Generar JWT token
        token_payload = {
            'sub': usuario.email,
            'user_id': usuario.id,
            'nombre': usuario.nombre,
            'rol': usuario.rol,
            'exp': datetime.utcnow() + timedelta(hours=24),
            'iat': datetime.utcnow()
        }
        
        token = jwt.encode(
            token_payload,
            os.getenv('SECRET_KEY', 'clave-secreta-temporal-12345'),
            algorithm='HS256'
        )
        
        # Actualizar sesión activa
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE usuarios 
            SET sesion_activa = TRUE, ultima_sesion = CURRENT_TIMESTAMP 
            WHERE id = %s
        """, (usuario.id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'access_token': token,
            'token_type': 'bearer',
            'user': {
                'id': usuario.id,
                'username': usuario.nombre,
                'email': usuario.email,
                'rol': usuario.rol
            }
        }), 200
        
    except Exception as e:
        print(f"❌ Error en jwt_verify_2fa: {str(e)}")
        return jsonify({'detail': f'Error en el servidor: {str(e)}'}), 500

# ===== VERIFICAR TOKEN =====
@auth_jwt_bp.route('/jwt/verify', methods=['GET'])
def verify_jwt_token():
    """Verificar si un token JWT es válido"""
    token = None
    
    if 'Authorization' in request.headers:
        auth_header = request.headers['Authorization']
        try:
            token = auth_header.split(" ")[1]
        except IndexError:
            return jsonify({'valid': False, 'error': 'Token mal formado'}), 401
    
    if not token:
        return jsonify({'valid': False, 'error': 'Token faltante'}), 401
    
    try:
        data = jwt.decode(
            token,
            os.getenv('SECRET_KEY', 'clave-secreta-temporal-12345'),
            algorithms=["HS256"]
        )
        return jsonify({
            'valid': True, 
            'user': {
                'email': data['sub'],
                'user_id': data['user_id'],
                'nombre': data['nombre'],
                'rol': data['rol']
            }
        }), 200
    except jwt.ExpiredSignatureError:
        return jsonify({'valid': False, 'error': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'valid': False, 'error': 'Token inválido'}), 401

# ===== LOGOUT JWT =====
@auth_jwt_bp.route('/jwt/logout', methods=['POST'])
@jwt_required
def jwt_logout(current_user):
    """Cerrar sesión (invalidar en BD)"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE usuarios SET sesion_activa = FALSE WHERE id = %s", 
            (current_user.id,)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Sesión cerrada exitosamente'
        }), 200
    except Exception as e:
        return jsonify({'error': f'Error al cerrar sesión: {str(e)}'}), 500

# ===== OBTENER PERFIL =====
@auth_jwt_bp.route('/jwt/me', methods=['GET'])
@jwt_required
def get_current_user(current_user):
    """Obtener información del usuario autenticado"""
    return jsonify({
        'id': current_user.id,
        'username': current_user.nombre,
        'email': current_user.email,
        'rol': current_user.rol
    }), 200

# ===== HEALTH CHECK =====
@auth_jwt_bp.route('/jwt/health', methods=['GET'])
def jwt_health():
    """Verificar que la API JWT está funcionando"""
    return jsonify({
        'status': 'healthy',
        'message': 'API JWT funcionando correctamente',
        'timestamp': datetime.utcnow().isoformat()
    }), 200