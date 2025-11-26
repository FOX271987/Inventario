from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify
from auth.decorators import admin_required, login_required, twofa_required
from auth.utils import (
    generar_codigo_verificacion, enviar_correo, verificar_conexion,
    obtener_direccion_desde_coordenadas, usuario_tiene_sesion_activa
)
from models.user import Usuario
import json
import time
import requests
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('users.listar_usuarios'))
    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        ubicacion_json = request.form.get('ubicacion')
        
        if not email or not password:
            flash('Todos los campos son obligatorios', 'error')
            return render_template('login.html')
        
        from utils.validation import validar_email
        if not validar_email(email):
            flash('Por favor ingresa un email válido', 'error')
            return render_template('login.html')
        
        try:
            sesion_activa = usuario_tiene_sesion_activa(email)

            if sesion_activa:
                flash('⚠️ Lo sentimos, este correo ya tiene una sesión activa en otro dispositivo.', 'error')
                return render_template('login.html')

            usuario = Usuario.verificar_login(email, password)
            if usuario:
                if ubicacion_json:
                    try:
                        ubicacion = json.loads(ubicacion_json)
                        info_direccion = obtener_direccion_desde_coordenadas(
                            ubicacion['latitud'], ubicacion['longitud']
                        )
                        
                        Usuario.guardar_ubicacion(
                            usuario.id,
                            ubicacion['latitud'],
                            ubicacion['longitud'],
                            ubicacion.get('precision'),
                            info_direccion['direccion'] if info_direccion else None,
                            info_direccion['ciudad'] if info_direccion else None,
                            info_direccion['pais'] if info_direccion else None
                        )
                        
                        session['user_ubicacion'] = {
                            'latitud': ubicacion['latitud'],
                            'longitud': ubicacion['longitud'],
                            'precision': ubicacion.get('precision'),
                            'direccion': info_direccion['direccion'] if info_direccion else None
                        }
                    except Exception as e:
                        print(f"Error procesando ubicación: {e}")
                
                session['user_id'] = usuario.id
                session['user_nombre'] = usuario.nombre
                session['user_email'] = usuario.email
                session['user_rol'] = usuario.rol
                session['twofa_verified'] = False
                
                codigo_verificacion = generar_codigo_verificacion()
                Usuario.guardar_codigo_verificacion(email, codigo_verificacion)
                
                tiene_conexion = verificar_conexion()
                
                if tiene_conexion:
                    asunto = "Código de verificación - Sistema de Seguridad"
                    cuerpo = f"""
                    Hola {usuario.nombre},
                    
                    Tu código de verificación para iniciar sesión es: {codigo_verificacion}
                    
                    Este código expirará en 5 minutos.
                    
                    Si no solicitaste este código, por favor ignora este mensaje.
                    
                    Saludos,
                    Equipo de Sistema de Seguridad
                    """
                    
                    if enviar_correo(email, asunto, cuerpo):
                        flash('Código de verificación enviado a tu correo electrónico', 'success')
                        return redirect(url_for('auth.verificar_2fa'))
                    else:
                        session['codigo_offline_2fa'] = codigo_verificacion
                        flash('Error al enviar el código. Revisa la consola de tu navegador para obtener el código.', 'warning')
                        return redirect(url_for('auth.verificar_2fa'))
                else:
                    session['codigo_offline_2fa'] = codigo_verificacion
                    flash('Modo offline: Revisa la consola de tu navegador para obtener el código de verificación', 'warning')
                    return redirect(url_for('auth.verificar_2fa'))
            else:
                flash('Email o contraseña incorrectos', 'error')
        except Exception as e:
            flash(f'Error al iniciar sesión: {str(e)}', 'error')
    
    return render_template('login.html')

@auth_bp.route('/verificar-2fa', methods=['GET', 'POST'])
def verificar_2fa():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    if session.get('twofa_verified', False):
        return redirect(url_for('users.listar_usuarios'))
    
    codigo_offline = session.get('codigo_offline_2fa', None)
    
    if request.method == 'POST':
        codigo = request.form['codigo']
        
        if codigo_offline:
            if codigo == codigo_offline:
                session['twofa_verified'] = True
                session.pop('codigo_offline_2fa', None)
                from utils.database import get_connection
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE usuarios 
                    SET sesion_activa = TRUE, ultima_sesion = CURRENT_TIMESTAMP 
                    WHERE id = %s
                """, (session['user_id'],))
                conn.commit()
                cursor.close()
                conn.close()
                flash('Verificación offline exitosa. ¡Bienvenido!', 'success')
                return redirect(url_for('users.listar_usuarios'))
            else:
                flash('Código de verificación inválido', 'error')
        else:
            if not codigo or len(codigo) != 6:
                flash('Por favor ingresa un código válido de 6 dígitos', 'error')
                return render_template('verificar_2fa.html', codigo_offline=codigo_offline)
            
            try:
                if Usuario.verificar_codigo(session['user_email'], codigo):
                    session['twofa_verified'] = True
                    from utils.database import get_connection
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                    UPDATE usuarios 
                    SET sesion_activa = TRUE, ultima_sesion = CURRENT_TIMESTAMP 
                    WHERE id = %s
                """, (session['user_id'],))
                    conn.commit()
                    cursor.close()
                    conn.close()
                    flash('Verificación exitosa. ¡Bienvenido!', 'success')
                    return redirect(url_for('users.listar_usuarios'))
                else:
                    flash('Código de verificación inválido o expirado', 'error')
            except Exception as e:
                flash(f'Error al verificar código: {str(e)}', 'error')
    
    return render_template('verificar_2fa.html', codigo_offline=codigo_offline)

@auth_bp.route('/reenviar-codigo')
def reenviar_codigo():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    codigo_verificacion = generar_codigo_verificacion()
    Usuario.guardar_codigo_verificacion(session['user_email'], codigo_verificacion)
    
    tiene_conexion = verificar_conexion()
    
    if tiene_conexion:
        asunto = "Nuevo código de verificación - Sistema de Seguridad"
        cuerpo = f"""
        Hola {session['user_nombre']},
        
        Tu nuevo código de verificación para iniciar sesión es: {codigo_verificacion}
        
        Este código expirará en 5 minutos.
        
        Si no solicitaste este código, por favor ignora este mensaje.
        
        Saludos,
        Equipo de Sistema de Seguridad
        """
        
        if enviar_correo(session['user_email'], asunto, cuerpo):
            flash('Nuevo código de verificación enviado a tu correo electrónico', 'success')
        else:
            session['codigo_offline_2fa'] = codigo_verificacion
            flash('Error al enviar el código. Revisa la consola de tu navegador para obtener el código.', 'warning')
    else:
        session['codigo_offline_2fa'] = codigo_verificacion
        flash('Modo offline: Revisa la consola de tu navegador para obtener el nuevo código', 'warning')
    
    return redirect(url_for('auth.verificar_2fa'))

@auth_bp.route('/olvide-contrasena', methods=['GET', 'POST'])
def olvide_contrasena():
    if request.method == 'POST':
        email = request.form['email']
        
        if not email or not validar_email(email):
            flash('Por favor ingresa un email válido', 'error')
            return render_template('olvide_contrasena.html')
        
        usuario = Usuario.obtener_por_email(email)
        if usuario:
            codigo_recuperacion = generar_codigo_verificacion()
            Usuario.guardar_codigo_verificacion(email, codigo_recuperacion)
            
            asunto = "Recuperación de contraseña - Sistema de Seguridad"
            cuerpo = f"""
            Hola {usuario.nombre},
            
            Has solicitado recuperar tu contraseña. Tu código de verificación es: {codigo_recuperacion}
            
            Este código expirará en 5 minutos.
            
            Si no solicitaste recuperar tu contraseña, por favor ignora este mensaje.
            
            Saludos,
            Equipo de Sistema de Seguridad
            """
            
            try:
                import socket
                socket.create_connection(("8.8.8.8", 53), timeout=3)
                tiene_conexion = True
            except OSError:
                tiene_conexion = False
            
            if tiene_conexion:
                if enviar_correo(email, asunto, cuerpo):
                    session['recovery_email'] = email
                    flash('Código de recuperación enviado a tu correo electrónico', 'success')
                    return redirect(url_for('auth.verificar_recuperacion'))
                else:
                    flash('Error al enviar el código de recuperación. Por favor contacta al administrador.', 'error')
            else:
                session['recovery_email'] = email
                session['codigo_offline'] = codigo_recuperacion
                flash('Modo offline: Revisa la consola de tu navegador para obtener el código de recuperación', 'warning')
                return redirect(url_for('auth.verificar_recuperacion'))
        else:
            flash('No existe una cuenta asociada a este email', 'error')
    
    return render_template('olvide_contrasena.html')

@auth_bp.route('/verificar-recuperacion', methods=['GET', 'POST'])
def verificar_recuperacion():
    if 'recovery_email' not in session:
        return redirect(url_for('auth.olvide_contrasena'))
    
    codigo_offline = session.get('codigo_offline', None)
    
    if request.method == 'POST':
        codigo = request.form['codigo']
        nueva_password = request.form['nueva_password']
        confirm_password = request.form['confirm_password']
        
        if codigo_offline:
            if codigo == codigo_offline:
                usuario = Usuario.obtener_por_email(session['recovery_email'])
                try:
                    Usuario.actualizar_password(usuario.id, nueva_password)
                    session.pop('recovery_email', None)
                    session.pop('codigo_offline', None)
                    flash('Contraseña actualizada exitosamente. Por favor inicia sesión.', 'success')
                    return redirect(url_for('auth.login'))
                except Exception as e:
                    flash(f'Error al actualizar contraseña: {str(e)}', 'error')
            else:
                flash('Código de verificación inválido', 'error')
        else:
            if not codigo or len(codigo) != 6:
                flash('Por favor ingresa un código válido de 6 dígitos', 'error')
                return render_template('verificar_recuperacion.html', codigo_offline=codigo_offline)
            
            if not nueva_password or len(nueva_password) < 6:
                flash('La nueva contraseña debe tener al menos 6 caracteres', 'error')
                return render_template('verificar_recuperacion.html', codigo_offline=codigo_offline)
            
            if nueva_password != confirm_password:
                flash('Las contraseñas no coinciden', 'error')
                return render_template('verificar_recuperacion.html', codigo_offline=codigo_offline)
            
            try:
                if Usuario.verificar_codigo(session['recovery_email'], codigo):
                    usuario = Usuario.obtener_por_email(session['recovery_email'])
                    Usuario.actualizar_password(usuario.id, nueva_password)
                    
                    session.pop('recovery_email', None)
                    flash('Contraseña actualizada exitosamente. Por favor inicia sesión.', 'success')
                    return redirect(url_for('auth.login'))
                else:
                    flash('Código de verificación inválido o expirado', 'error')
            except Exception as e:
                flash(f'Error al actualizar contraseña: {str(e)}', 'error')
    
    return render_template('verificar_recuperacion.html', codigo_offline=codigo_offline)

@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if 'user_id' in session:
        return redirect(url_for('users.listar_usuarios'))
    
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        from utils.validation import validar_nombre, validar_password, validar_email
        
        if not all([nombre, email, password, confirm_password]):
            flash('Todos los campos son obligatorios', 'error')
            return render_template('registro.html')
        
        es_valido, mensaje_error = validar_nombre(nombre)
        if not es_valido:
            flash(mensaje_error, 'error')
            return render_template('registro.html')
        
        if not validar_email(email):
            flash('Por favor ingresa un email válido', 'error')
            return render_template('registro.html')
        
        es_valida, mensaje_error = validar_password(password)
        if not es_valida:
            flash(mensaje_error, 'error')
            return render_template('registro.html')
        
        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'error')
            return render_template('registro.html')
        
        try:
            usuario_id = Usuario.crear(nombre, email, password)
            flash('Registro exitoso. Por favor inicia sesión.', 'success')
            return redirect(url_for('auth.login'))
        except ValueError as e:
            flash(str(e), 'error')
        except Exception as e:
            flash(f'Error al registrar usuario: {str(e)}', 'error')
    
    return render_template('registro.html')

@auth_bp.route('/login/google')
def login_google():
    redirect_uri = url_for('auth.auth_google', _external=True)
    from app_simple import google
    return google.authorize_redirect(redirect_uri)

@auth_bp.route('/auth/google')
def auth_google():
    try:
        from app_simple import google
        token = google.authorize_access_token()
        
        max_retries = 3
        userinfo = None
        
        for attempt in range(max_retries):
            try:
                userinfo = token.get('userinfo')
                if not userinfo:
                    response = requests.get(
                        'https://www.googleapis.com/oauth2/v2/userinfo',
                        headers={'Authorization': f'Bearer {token["access_token"]}'},
                        timeout=10
                    )
                    if response.status_code == 200:
                        userinfo = response.json()
                    else:
                        raise Exception(f"Error HTTP {response.status_code}")
                break
            except Exception as e:
                print(f"Intento {attempt + 1} fallido: {e}")
                if attempt == max_retries - 1:
                    raise e
                time.sleep(1)
        
        if not userinfo:
            raise Exception("No se pudo obtener información del usuario")
        
        email = userinfo.get('email')
        nombre = userinfo.get('name', 'Usuario Google')
        
        if not email:
            raise Exception("No se pudo obtener el email del usuario")
        
        usuario = Usuario.obtener_por_email(email)
        if not usuario:
            usuario_id = Usuario.crear_social(nombre, email, 'google')
            usuario = Usuario.obtener_por_id(usuario_id)
        
        codigo_verificacion = generar_codigo_verificacion()
        Usuario.guardar_codigo_verificacion(email, codigo_verificacion)
        
        asunto = "Código de verificación - Inicio de sesión con Google"
        cuerpo = f"""
        Hola {nombre},
        
        Has iniciado sesión con tu cuenta de Google. Tu código de verificación es: {codigo_verificacion}
        
        Este código expirará en 5 minutos.
        
        Si no realizaste esta acción, por favor contacta al administrador.
        
        Saludos,
        Equipo de Sistema de Seguridad
        """
        
        enviar_correo(email, asunto, cuerpo)
        
        session['social_auth'] = {
            'email': email,
            'nombre': nombre,
            'proveedor': 'google',
            'user_id': usuario.id
        }
        
        flash('Código de verificación enviado. Revisa tu correo.', 'info')
        return redirect(url_for('auth.verificar_social'))
        
    except Exception as e:
        print(f"Error detallado en OAuth: {e}")
        flash(f'Error en autenticación con Google: {str(e)}', 'error')
        return redirect(url_for('auth.login'))

@auth_bp.route('/verificar-social', methods=['GET', 'POST'])
def verificar_social():
    if 'social_auth' not in session:
        return redirect(url_for('auth.login'))
    
    codigo_simulado = session.get('codigo_simulado', None)
    
    if request.method == 'POST':
        codigo = request.form['codigo']
        email = session['social_auth']['email']
        
        if codigo_simulado and codigo == codigo_simulado:
            usuario = Usuario.obtener_por_email(email)
            
            session['user_id'] = usuario.id
            session['user_nombre'] = usuario.nombre
            session['user_email'] = usuario.email
            session['user_rol'] = usuario.rol
            session['twofa_verified'] = True
            
            session.pop('social_auth', None)
            session.pop('codigo_simulado', None)
            
            flash(f'¡Bienvenido {usuario.nombre}!', 'success')
            return redirect(url_for('users.listar_usuarios'))
        
        if Usuario.verificar_codigo(email, codigo):
            usuario = Usuario.obtener_por_email(email)
            
            session['user_id'] = usuario.id
            session['user_nombre'] = usuario.nombre
            session['user_email'] = usuario.email
            session['user_rol'] = usuario.rol
            session['twofa_verified'] = True
            
            session.pop('social_auth', None)
            
            flash(f'¡Bienvenido {usuario.nombre}!', 'success')
            return redirect(url_for('users.listar_usuarios'))
        else:
            flash('Código de verificación inválido o expirado', 'error')
    
    return render_template('verificar_social.html', codigo_simulado=codigo_simulado)

@auth_bp.route('/api/reenviar-codigo-social', methods=['POST'])
def reenviar_codigo_social():
    try:
        if 'social_auth' not in session:
            return jsonify({'success': False, 'message': 'Sesión no válida'})
        
        email = session['social_auth']['email']
        nombre = session['social_auth']['nombre']
        
        codigo_verificacion = generar_codigo_verificacion()
        Usuario.guardar_codigo_verificacion(email, codigo_verificacion)
        
        asunto = "Nuevo código de verificación"
        cuerpo = f"""
        Hola {nombre},
        
        Tu nuevo código de verificación es: {codigo_verificacion}
        
        Este código expirará en 5 minutos.
        
        Saludos,
        Equipo de Sistema de Seguridad
        """
        
        if enviar_correo(email, asunto, cuerpo):
            return jsonify({'success': True, 'message': 'Código reenviado'})
        else:
            return jsonify({'success': False, 'message': 'Error al enviar correo'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@auth_bp.route('/logout')
def logout():
    user_id = session.get('user_id')
    user_email = session.get('user_email')
    
    if user_id:
        try:
            from utils.database import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE usuarios SET sesion_activa = FALSE WHERE id = %s", (user_id,))
            conn.commit()
            cursor.close()
            conn.close()
            print(f"✅ Sesión cerrada para usuario ID: {user_id}, Email: {user_email}")
        except Exception as e:
            print(f"❌ Error al actualizar estado de sesión: {e}")
    
    session.clear()
    flash('Sesión cerrada exitosamente', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/forzar-logout/<email>')
@login_required
@twofa_required
@admin_required
def forzar_logout(email):
    try:
        from utils.database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE usuarios SET sesion_activa = FALSE WHERE email = %s", (email,))
        conn.commit()
        cursor.close()
        conn.close()
        
        flash(f'Sesión forzada cerrada para {email}', 'success')
    except Exception as e:
        flash(f'Error al forzar cierre de sesión: {str(e)}', 'error')
    
    return redirect(url_for('users.listar_usuarios'))

def validar_email(email):
    """Validar formato de email"""
    import re
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(patron, email) is not None