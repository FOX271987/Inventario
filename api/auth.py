from flask import Blueprint, request, jsonify, session
from auth.decorators import login_required, twofa_required, admin_required, editor_required
from models.user import Usuario
from auth.utils import generar_codigo_verificacion, enviar_correo, verificar_conexion
from utils.validation import validar_nombre, validar_password, validar_email
from utils.database import get_connection

api_auth_bp = Blueprint('api_auth', __name__)

@api_auth_bp.route('/auth/login', methods=['POST'])
def api_login():
    """Endpoint de login para API"""
    try:
        if not request.is_json:
            return jsonify({'error': 'Content-Type debe ser application/json'}), 400
            
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Datos JSON requeridos'}), 400
        
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email y contraseña son requeridos'}), 400
        
        if not isinstance(email, str) or not isinstance(password, str):
            return jsonify({'error': 'Email y contraseña deben ser cadenas de texto'}), 400
        
        if not validar_email(email):
            return jsonify({'error': 'Formato de email inválido'}), 400
        
        es_valida, mensaje_error = validar_password(password)
        if not es_valida:
            return jsonify({'error': mensaje_error}), 400
        
        from auth.utils import usuario_tiene_sesion_activa
        sesion_activa = usuario_tiene_sesion_activa(email)
        
        if sesion_activa:
            return jsonify({
                'error': 'Lo sentimos, este correo ya tiene una sesión activa en otro dispositivo. Cierre la sesión en el otro dispositivo antes de intentar nuevamente.'
            }), 403
        
        usuario = Usuario.verificar_login(email, password)
        if not usuario:
            return jsonify({'error': 'Credenciales incorrectas'}), 401        
        
        codigo_verificacion = generar_codigo_verificacion()
        exito_guardado = Usuario.guardar_codigo_verificacion(email, codigo_verificacion)
        
        if not exito_guardado:
            return jsonify({'error': 'Error al generar código de verificación'}), 500
        
        tiene_conexion = verificar_conexion()
        
        response_data = {
            'success': True,
            'message': 'Código de verificación generado',
            'user_id': usuario.id,
            'user_nombre': usuario.nombre,
            'user_email': usuario.email,
            'user_rol': usuario.rol,
            'requires_2fa': True
        }
        
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
        error_message = f'Error interno del servidor: {str(e)}'
        print(f"Exception en api_login (email: {email}): {error_message}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@api_auth_bp.route('/auth/verify-2fa', methods=['POST'])
def api_verify_2fa():
    """Endpoint para verificación de 2FA"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Datos JSON requeridos'}), 400
        
        email = data.get('email')
        codigo = data.get('codigo')
        
        if not email or not codigo:
            return jsonify({'error': 'Email y código son requeridos'}), 400
        
        if Usuario.verificar_codigo(email, codigo):
            usuario = Usuario.obtener_por_email(email)
            if usuario:
                session['user_id'] = usuario.id
                session['user_nombre'] = usuario.nombre
                session['user_email'] = usuario.email
                session['user_rol'] = usuario.rol
                session['twofa_verified'] = True
                session['api_auth'] = True
                
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
                    'success': True,
                    'message': 'Verificación 2FA exitosa',
                    'user': {
                        'id': usuario.id,
                        'nombre': usuario.nombre,
                        'email': usuario.email,
                        'rol': usuario.rol
                    },
                    'session_id': f"api_{usuario.id}_{datetime.now().timestamp()}"
                }), 200
            else:
                return jsonify({'error': 'Usuario no encontrado'}), 404
        else:
            return jsonify({'error': 'Código de verificación inválido o expirado'}), 401
            
    except Exception as e:
        return jsonify({'error': f'Error en el servidor: {str(e)}'}), 500

@api_auth_bp.route('/auth/logout', methods=['POST'])
def api_logout():
    """Endpoint para cerrar sesión"""
    if 'user_id' in session:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE usuarios SET sesion_activa = FALSE WHERE id = %s", (session['user_id'],))
        conn.commit()
        cursor.close()
        conn.close()
    
    session.clear()
    return jsonify({
        'success': True,
        'message': 'Sesión cerrada exitosamente'
    }), 200

@api_auth_bp.route('/auth/register', methods=['POST'])
def api_register():
    """Endpoint para registro de usuarios"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Datos JSON requeridos'}), 400
        
        nombre = data.get('nombre')
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        rol = data.get('rol', 'lector')
        
        if not all([nombre, email, password, confirm_password]):
            return jsonify({'error': 'Todos los campos son obligatorios'}), 400
        
        es_valido, mensaje_error = validar_nombre(nombre)
        if not es_valido:
            return jsonify({'error': mensaje_error}), 400
        
        if not validar_email(email):
            return jsonify({'error': 'Formato de email inválido'}), 400
        
        es_valida, mensaje_error = validar_password(password)
        if not es_valida:
            return jsonify({'error': mensaje_error}), 400
        
        if password != confirm_password:
            return jsonify({'error': 'Las contraseñas no coinciden'}), 400
        
        if rol not in ['admin', 'editor', 'lector']:
            return jsonify({'error': 'Rol no válido'}), 400
        
        try:
            usuario_id = Usuario.crear(nombre, email, password, rol)
            return jsonify({
                'success': True,
                'message': 'Usuario registrado exitosamente',
                'user_id': usuario_id
            }), 201
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
            
    except Exception as e:
        return jsonify({'error': f'Error en el servidor: {str(e)}'}), 500

@api_auth_bp.route('/auth/forgot-password', methods=['POST'])
def api_forgot_password():
    """Endpoint para recuperación de contraseña"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Datos JSON requeridos'}), 400
        
        email = data.get('email')
        if not email:
            return jsonify({'error': 'Email es requerido'}), 400
        
        usuario = Usuario.obtener_por_email(email)
        if not usuario:
            return jsonify({'error': 'No existe una cuenta con este email'}), 404
        
        codigo_recuperacion = generar_codigo_verificacion()
        Usuario.guardar_codigo_verificacion(email, codigo_recuperacion)
        
        tiene_conexion = verificar_conexion()
        response_data = {
            'success': True,
            'message': 'Código de recuperación generado'
        }
        
        if tiene_conexion:
            asunto = "Recuperación de contraseña - Sistema de Seguridad"
            cuerpo = f"""
            Hola {usuario.nombre},
            
            Tu código de recuperación es: {codigo_recuperacion}
            
            Este código expirará en 5 minutos.
            """
            if enviar_correo(email, asunto, cuerpo):
                response_data['message'] = 'Código de recuperación enviado por correo'
            else:
                response_data['codigo_offline'] = codigo_recuperacion
                response_data['message'] = 'Error al enviar correo, use el código offline'
        else:
            response_data['codigo_offline'] = codigo_recuperacion
            response_data['message'] = 'Modo offline: use el código proporcionado'
        
        session['recovery_email'] = email
        
        return jsonify(response_data), 200
        
    except Exception as e:
        return jsonify({'error': f'Error en el servidor: {str(e)}'}), 500

@api_auth_bp.route('/auth/verify-reset-code', methods=['POST'])
def api_verify_reset_code():
    """Endpoint para verificar código de restablecimiento"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Datos JSON requeridos'}), 400
        
        email = data.get('email')
        codigo = data.get('codigo')
        
        if not email or not codigo:
            return jsonify({'error': 'Email y código son requeridos'}), 400
        
        usuario = Usuario.obtener_por_email(email)
        if not usuario:
            return jsonify({'error': 'No existe una cuenta con este email'}), 404
        
        if Usuario.verificar_codigo(email, codigo):
            from datetime import datetime, timezone, timedelta
            
            session['reset_email'] = email
            session['reset_verified'] = True
            session['reset_expires'] = datetime.now(timezone.utc) + timedelta(minutes=10)
            
            return jsonify({
                'success': True,
                'message': 'Código verificado correctamente',
                'codigo_valido': True,
                'next_step': 'Puede proceder a restablecer la contraseña'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Código inválido o expirado',
                'codigo_valido': False,
                'sugerencia': 'Solicite un nuevo código de recuperación'
            }), 400
            
    except Exception as e:
        return jsonify({'error': f'Error al verificar código: {str(e)}'}), 500

@api_auth_bp.route('/auth/reset-password', methods=['POST'])
def api_reset_password():
    """Endpoint para restablecer contraseña"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Datos JSON requeridos'}), 400
        
        email = data.get('email')
        codigo = data.get('codigo')
        nueva_password = data.get('nueva_password')
        confirm_password = data.get('confirm_password')
        
        if not all([email, codigo, nueva_password, confirm_password]):
            return jsonify({'error': 'Todos los campos son requeridos'}), 400
        
        if nueva_password != confirm_password:
            return jsonify({'error': 'Las contraseñas no coinciden'}), 400
        
        if len(nueva_password) < 6:
            return jsonify({'error': 'La nueva contraseña debe tener al menos 6 caracteres'}), 400
        
        usuario = Usuario.obtener_por_email(email)
        if not usuario:
            return jsonify({'error': 'No existe una cuenta con este email'}), 404
        
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT id FROM codigos_verificacion WHERE email = %s AND codigo = %s AND expiracion > NOW() AND usado = FALSE",
                (email, codigo)
            )
            resultado = cursor.fetchone()
            
            if not resultado:
                return jsonify({'error': 'Código de verificación inválido o expirado'}), 400
            
            Usuario.actualizar_password(usuario.id, nueva_password)
            
            cursor.execute(
                "UPDATE codigos_verificacion SET usado = TRUE WHERE id = %s",
                (resultado[0],)
            )
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': 'Contraseña restablecida exitosamente',
                'user_email': email
            }), 200
            
        except Exception as e:
            conn.rollback()
            return jsonify({'error': f'Error en la base de datos: {str(e)}'}), 500
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        return jsonify({'error': f'Error al restablecer contraseña: {str(e)}'}), 500

@api_auth_bp.route('/auth/password-recovery', methods=['POST'])
def api_password_recovery():
    """Endpoint unificado para recuperación de contraseña"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Datos JSON requeridos'}), 400
        
        action = data.get('action')
        email = data.get('email')
        
        if action == 'request':
            if not email:
                return jsonify({'error': 'Email es requerido'}), 400
            
            usuario = Usuario.obtener_por_email(email)
            if not usuario:
                return jsonify({'error': 'No existe una cuenta con este email'}), 404
            
            codigo_recuperacion = generar_codigo_verificacion()
            Usuario.guardar_codigo_verificacion(email, codigo_recuperacion)
            
            tiene_conexion = verificar_conexion()
            response_data = {
                'success': True,
                'message': 'Código de recuperación generado',
                'action': 'request'
            }
            
            if tiene_conexion:
                asunto = "Código de recuperación - Sistema de Seguridad"
                cuerpo = f"Tu código de recuperación es: {codigo_recuperacion}"
                if enviar_correo(email, asunto, cuerpo):
                    response_data['message'] = 'Código enviado por correo electrónico'
                else:
                    response_data['codigo_offline'] = codigo_recuperacion
            else:
                response_data['codigo_offline'] = codigo_recuperacion
                response_data['message'] = 'Modo offline: use el código proporcionado'
            
            session['recovery_email'] = email
            return jsonify(response_data), 200
        
        elif action == 'verify':
            codigo = data.get('codigo')
            if not email or not codigo:
                return jsonify({'error': 'Email y código son requeridos'}), 400
            
            if Usuario.verificar_codigo(email, codigo):
                session['recovery_verified'] = True
                return jsonify({
                    'success': True,
                    'message': 'Código verificado correctamente',
                    'action': 'verify'
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'message': 'Código inválido o expirado',
                    'action': 'verify'
                }), 400
        
        elif action == 'reset':
            if not session.get('recovery_verified'):
                return jsonify({'error': 'Debe verificar el código primero'}), 400
            
            codigo = data.get('codigo')
            nueva_password = data.get('nueva_password')
            confirm_password = data.get('confirm_password')
            
            if not all([codigo, nueva_password, confirm_password]):
                return jsonify({'error': 'Todos los campos son requeridos'}), 400
            
            if nueva_password != confirm_password:
                return jsonify({'error': 'Las contraseñas no coinciden'}), 400
            
            if len(nueva_password) < 6:
                return jsonify({'error': 'La contraseña debe tener al menos 6 caracteres'}), 400
            
            email = session.get('recovery_email')
            if Usuario.verificar_codigo(email, codigo):
                usuario = Usuario.obtener_por_email(email)
                Usuario.actualizar_password(usuario.id, nueva_password)
                
                session.pop('recovery_email', None)
                session.pop('recovery_verified', None)
                
                return jsonify({
                    'success': True,
                    'message': 'Contraseña restablecida exitosamente',
                    'action': 'reset'
                }), 200
            else:
                return jsonify({'error': 'Código de verificación inválido'}), 400
        
        else:
            return jsonify({'error': 'Acción no válida. Use: request, verify o reset'}), 400
            
    except Exception as e:
        return jsonify({'error': f'Error en recuperación de contraseña: {str(e)}'}), 500

@api_auth_bp.route('/health')
def health_check():
    """Endpoint de salud para verificar que la API está funcionando"""
    from datetime import datetime
    return jsonify({
        'status': 'healthy',
        'message': 'Sistema de Seguridad API está funcionando correctamente',
        'timestamp': datetime.now().isoformat()
    })

@api_auth_bp.route('/connection/status')
def connection_status():
    """Verificar estado de conexión"""
    tiene_conexion = verificar_conexion()
    return jsonify({
        'online': tiene_conexion,
        'modo_operacion': 'online' if tiene_conexion else 'offline',
        'servicios_disponibles': 'completos' if tiene_conexion else 'limitados'
    })

from datetime import datetime