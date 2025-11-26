import random
import string
import requests
import os
from datetime import datetime, timedelta
from utils.database import get_connection

# Configuración de Brevo (usando tus nombres de variables)
BREVO_API_KEY = os.getenv('BREVO_API_KEY', '')
BREVO_SENDER_EMAIL = os.getenv('FROM_EMAIL', 'noreply@tudominio.com')
BREVO_SENDER_NAME = os.getenv('FROM_NAME', 'Sistema de Inventario')


def generar_codigo_verificacion(longitud=6):
    """Generar código de verificación aleatorio"""
    return ''.join(random.choices(string.digits, k=longitud))


def enviar_correo_brevo(destinatario, asunto, cuerpo_html):
    """Enviar correo usando la API de Brevo"""
    try:
        if not BREVO_API_KEY:
            print(f"📧 SIMULACIÓN (sin API key) - Para: {destinatario}")
            print(f"📧 Asunto: {asunto}")
            return True
        
        import sib_api_v3_sdk
        from sib_api_v3_sdk.rest import ApiException
        
        # Configurar API
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = BREVO_API_KEY
        
        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
        
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": destinatario}],
            sender={"name": BREVO_SENDER_NAME, "email": BREVO_SENDER_EMAIL},
            subject=asunto,
            html_content=cuerpo_html
        )
        
        api_response = api_instance.send_transac_email(send_smtp_email)
        print(f"✅ Correo enviado exitosamente a: {destinatario} (ID: {api_response.message_id})")
        return True
        
    except ApiException as e:
        print(f"❌ Error de Brevo API enviando a {destinatario}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error enviando correo a {destinatario}: {e}")
        return False


def enviar_correo(destinatario, asunto, cuerpo):
    """Enviar correo electrónico (wrapper para compatibilidad)"""
    # Convertir texto plano a HTML básico si es necesario
    if not cuerpo.strip().startswith('<'):
        cuerpo_html = f"<p>{cuerpo.replace(chr(10), '<br>')}</p>"
    else:
        cuerpo_html = cuerpo
    
    return enviar_correo_brevo(destinatario, asunto, cuerpo_html)


def enviar_notificacion_inventario(destinatario, asunto, cuerpo, tipo_notificacion="inventario"):
    """Enviar notificación de inventario por correo con plantilla mejorada"""
    try:
        # Plantilla HTML mejorada para notificaciones
        cuerpo_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #f8f9fa; padding: 20px; text-align: center; border-radius: 5px; }}
                .content {{ background: white; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
                .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #666; }}
                .alert {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; }}
                .success {{ background: #d1edff; border: 1px solid #b3d7ff; padding: 15px; border-radius: 5px; }}
                .warning {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; }}
                .danger {{ background: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🔔 Sistema de Inventario - Notificación</h2>
                </div>
                <div class="content">
                    {cuerpo}
                </div>
                <div class="footer">
                    <p>Este es un mensaje automático del Sistema de Inventario.</p>
                    <p>© {datetime.now().year} Sistema de Seguridad</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return enviar_correo_brevo(destinatario, asunto, cuerpo_html)
        
    except Exception as e:
        print(f"❌ Error enviando notificación a {destinatario}: {e}")
        return False


def obtener_correos_administradores():
    """Obtener lista de correos de administradores para notificaciones"""
    try:
        from app_simple import app
        with app.app_context():
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM usuarios WHERE rol = 'admin' AND email IS NOT NULL")
            administradores = [row[0] for row in cursor.fetchall()]
            cursor.close()
            conn.close()
            return administradores
    except Exception as e:
        print(f"Error obteniendo correos de administradores: {e}")
        return []


def obtener_correos_editores():
    """Obtener lista de correos de editores para notificaciones"""
    try:
        from app_simple import app
        with app.app_context():
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM usuarios WHERE rol IN ('admin', 'editor') AND email IS NOT NULL")
            editores = [row[0] for row in cursor.fetchall()]
            cursor.close()
            conn.close()
            return editores
    except Exception as e:
        print(f"Error obteniendo correos de editores: {e}")
        return []


def obtener_correos_por_rol(rol=None):
    """Obtener correos de usuarios filtrados por rol"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        if rol:
            cursor.execute("""
                SELECT email, nombre, rol 
                FROM usuarios 
                WHERE rol = %s 
                AND email IS NOT NULL 
                AND email != ''
                ORDER BY nombre
            """, (rol,))
        else:
            cursor.execute("""
                SELECT email, nombre, rol 
                FROM usuarios 
                WHERE email IS NOT NULL 
                AND email != ''
                ORDER BY rol DESC, nombre
            """)
        
        usuarios = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return [{'email': row[0], 'nombre': row[1], 'rol': row[2]} for row in usuarios]
        
    except Exception as e:
        print(f"❌ Error obteniendo correos por rol: {e}")
        return []


def enviar_notificacion_masiva(destinatarios, asunto, cuerpo, tipo_notificacion="sistema"):
    """Enviar notificación a múltiples destinatarios"""
    exitosos = 0
    fallidos = 0
    
    print(f"📧 Iniciando envío masivo a {len(destinatarios)} destinatario(s)...")
    
    for destinatario in destinatarios:
        if enviar_notificacion_inventario(destinatario, asunto, cuerpo, tipo_notificacion):
            exitosos += 1
        else:
            fallidos += 1
    
    print(f"📧 Envío completado: {exitosos} exitoso(s), {fallidos} fallido(s)")
    return {'exitosos': exitosos, 'fallidos': fallidos, 'total': len(destinatarios)}


def verificar_conexion():
    """Verificar si hay conexión a internet"""
    try:
        response = requests.get("https://www.google.com", timeout=5)
        return response.status_code == 200
    except:
        return False


def obtener_direccion_desde_coordenadas(lat, lon):
    """Obtener información de dirección a partir de coordenadas usando Nominatim"""
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=18&addressdetails=1"
        headers = {'User-Agent': 'SistemaSeguridadApp/1.0'}
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data and 'address' in data:
                address = data['address']
                return {
                    'direccion': data.get('display_name', ''),
                    'ciudad': address.get('city') or address.get('town') or address.get('village') or address.get('municipality', ''),
                    'pais': address.get('country', '')
                }
        
        return None
        
    except Exception as e:
        print(f"Error obteniendo dirección: {e}")
        return None


def usuario_tiene_sesion_activa(email):
    """Verificar si el usuario ya tiene una sesión activa"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id, nombre, sesion_activa, ultima_sesion 
            FROM usuarios 
            WHERE email = %s AND sesion_activa = TRUE
        """, (email,))
        
        resultado = cursor.fetchone()
        
        if resultado:
            user_id, nombre, sesion_activa, ultima_sesion = resultado
            
            if ultima_sesion:
                tiempo_expiracion = timedelta(hours=24)
                
                if datetime.now() - ultima_sesion > tiempo_expiracion:
                    cursor.execute("UPDATE usuarios SET sesion_activa = FALSE WHERE id = %s", (user_id,))
                    conn.commit()
                    return False
            
            return True
        
        return False
        
    except Exception as e:
        print(f"Error verificando sesión activa: {e}")
        return False
        
    finally:
        cursor.close()
        conn.close()