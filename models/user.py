from utils.database import get_connection
from utils.validation import encriptar_password, verificar_password
from datetime import datetime, timedelta

class Usuario:
    def __init__(self, id, nombre, email, password, rol):
        self.id = id
        self.nombre = nombre
        self.email = email
        self.password = password
        self.rol = rol
    
    @classmethod
    def obtener_todos(cls):
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT id, nombre, email, password, rol FROM usuarios ORDER BY id")
            usuarios = [cls(*row) for row in cursor.fetchall()]
            return usuarios
        finally:
            cursor.close()
            conn.close()
    
    @classmethod
    def obtener_con_filtros(cls, nombre=None, rol=None):
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            query = "SELECT id, nombre, email, password, rol FROM usuarios"
            params = []
            
            if nombre or rol:
                query += " WHERE"
                conditions = []
                
                if nombre:
                    conditions.append(" nombre ILIKE %s")
                    params.append(f'%{nombre}%')
                
                if rol:
                    conditions.append(" rol = %s")
                    params.append(rol)
                
                query += " AND".join(conditions)
            
            query += " ORDER BY id"
            cursor.execute(query, params)
            usuarios = [cls(*row) for row in cursor.fetchall()]
            return usuarios
        finally:
            cursor.close()
            conn.close()
    
    @classmethod
    def crear(cls, nombre, email, password, rol='lector'):
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT COUNT(*) FROM usuarios WHERE email = %s", (email,))
            if cursor.fetchone()[0] > 0:
                raise ValueError("El email ya está registrado")
            
            if len(password) < 6:
                raise ValueError("La contraseña debe tener al menos 6 caracteres")
            
            password_encriptada = encriptar_password(password)
            
            cursor.execute(
                "INSERT INTO usuarios (nombre, email, password, rol) VALUES (%s, %s, %s, %s) RETURNING id",
                (nombre, email, password_encriptada, rol)
            )
            nuevo_id = cursor.fetchone()[0]
            conn.commit()
            return nuevo_id
        except Exception as e:
            conn.rollback()
            if 'duplicate key value' in str(e).lower():
                raise ValueError("El email ya está registrado")
            raise ValueError(f"Error al crear usuario: {str(e)}")
        finally:
            cursor.close()
            conn.close()
    
    @classmethod
    def actualizar(cls, id, nombre, email, rol, password=None):
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT COUNT(*) FROM usuarios WHERE email = %s AND id != %s", (email, id))
            if cursor.fetchone()[0] > 0:
                raise ValueError("El email ya está registrado en otro usuario")
            
            if password:
                if len(password) < 6:
                    raise ValueError("La contraseña debe tener al menos 6 caracteres")
                
                password_encriptada = encriptar_password(password)
                cursor.execute(
                    "UPDATE usuarios SET nombre = %s, email = %s, rol = %s, password = %s WHERE id = %s",
                    (nombre, email, rol, password_encriptada, id)
                )
            else:
                cursor.execute(
                    "UPDATE usuarios SET nombre = %s, email = %s, rol = %s WHERE id = %s",
                    (nombre, email, rol, id)
                )
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise ValueError(f"Error al actualizar: {str(e)}")
        finally:
            cursor.close()
            conn.close()
    
    @classmethod
    def actualizar_password(cls, id, nueva_password):
        """Actualizar solo la contraseña"""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            if len(nueva_password) < 6:
                raise ValueError("La contraseña debe tener al menos 6 caracteres")
            
            password_encriptada = encriptar_password(nueva_password)
            
            cursor.execute(
                "UPDATE usuarios SET password = %s WHERE id = %s",
                (password_encriptada, id)
            )
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise ValueError(f"Error al actualizar contraseña: {str(e)}")
        finally:
            cursor.close()
            conn.close()
    
    @classmethod
    def eliminar(cls, id):
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM usuarios WHERE id = %s", (id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise ValueError(f"Error al eliminar: {str(e)}")
        finally:
            cursor.close()
            conn.close()
    
    @classmethod
    def email_existe(cls, email):
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT COUNT(*) FROM usuarios WHERE email = %s", (email,))
            existe = cursor.fetchone()[0] > 0
            return existe
        finally:
            cursor.close()
            conn.close()
    
    @classmethod
    def obtener_por_id(cls, id):
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT id, nombre, email, password, rol FROM usuarios WHERE id = %s", (id,))
            row = cursor.fetchone()
            if row:
                return cls(*row)
            return None
        finally:
            cursor.close()
            conn.close()
    
    @classmethod
    def obtener_por_email(cls, email):
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT id, nombre, email, password, rol FROM usuarios WHERE email = %s", (email,))
            row = cursor.fetchone()
            if row:
                return cls(*row)
            return None
        finally:
            cursor.close()
            conn.close()
    
    @classmethod
    def verificar_login(cls, email, password):
        """Verificar credenciales de login"""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT id, nombre, email, password, rol FROM usuarios WHERE email = %s", (email,))
            row = cursor.fetchone()
            if row:
                usuario = cls(*row)
                if verificar_password(password, usuario.password):
                    return usuario
            return None
        finally:
            cursor.close()
            conn.close()
    
    @classmethod
    def guardar_codigo_verificacion(cls, email, codigo):
        """Guardar código de verificación en la base de datos"""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS codigos_verificacion (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(150) NOT NULL,
                    codigo VARCHAR(10) NOT NULL,
                    expiracion TIMESTAMP NOT NULL,
                    usado BOOLEAN DEFAULT FALSE,
                    creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute("DELETE FROM codigos_verificacion WHERE expiracion < NOW()")
            
            expiracion = datetime.now() + timedelta(minutes=5)
            cursor.execute(
                "INSERT INTO codigos_verificacion (email, codigo, expiracion) VALUES (%s, %s, %s)",
                (email, codigo, expiracion)
            )
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error guardando código de verificación: {e}")
            return False
        finally:
            cursor.close()
            conn.close()
    
    @classmethod
    def verificar_codigo(cls, email, codigo):
        """Verificar si el código es válido"""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT id FROM codigos_verificacion WHERE email = %s AND codigo = %s AND expiracion > NOW() AND usado = FALSE",
                (email, codigo)
            )
            resultado = cursor.fetchone()
            
            if resultado:
                cursor.execute(
                    "UPDATE codigos_verificacion SET usado = TRUE WHERE id = %s",
                    (resultado[0],)
                )
                conn.commit()
                return True
            return False
        except Exception as e:
            conn.rollback()
            print(f"Error verificando código: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

    @classmethod
    def crear_social(cls, nombre, email, proveedor):
        """Crear usuario desde autenticación social"""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT COUNT(*) FROM usuarios WHERE email = %s", (email,))
            if cursor.fetchone()[0] > 0:
                cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
                return cursor.fetchone()[0]
            
            from auth.utils import generar_codigo_verificacion
            password_aleatoria = generar_codigo_verificacion(12)
            password_encriptada = encriptar_password(password_aleatoria)
            
            rol = 'lector'
            
            cursor.execute(
                "INSERT INTO usuarios (nombre, email, password, rol) VALUES (%s, %s, %s, %s) RETURNING id",
                (nombre, email, password_encriptada, rol)
            )
            nuevo_id = cursor.fetchone()[0]
            conn.commit()
            return nuevo_id
        except Exception as e:
            conn.rollback()
            raise ValueError(f"Error al crear usuario social: {str(e)}")
        finally:
            cursor.close()
            conn.close()
    
    @classmethod
    def guardar_ubicacion(cls, usuario_id, latitud, longitud, precision_metros=None, direccion=None, ciudad=None, pais=None):
        """Guardar la ubicación del usuario en la base de datos"""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT id FROM ubicaciones_usuarios WHERE usuario_id = %s",
                (usuario_id,)
            )
            existe = cursor.fetchone()
            
            if existe:
                cursor.execute(
                    """UPDATE ubicaciones_usuarios 
                    SET latitud = %s, longitud = %s, precision_metros = %s, 
                        direccion = %s, ciudad = %s, pais = %s, actualizado = CURRENT_TIMESTAMP
                    WHERE usuario_id = %s""",
                    (latitud, longitud, precision_metros, direccion, ciudad, pais, usuario_id)
                )
            else:
                cursor.execute(
                    """INSERT INTO ubicaciones_usuarios 
                    (usuario_id, latitud, longitud, precision_metros, direccion, ciudad, pais)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (usuario_id, latitud, longitud, precision_metros, direccion, ciudad, pais)
                )
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error guardando ubicación: {e}")
            return False
        finally:
            cursor.close()
            conn.close()
    
    @classmethod
    def obtener_ultima_ubicacion(cls, usuario_id):
        """Obtener la última ubicación registrada del usuario"""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """SELECT latitud, longitud, precision_metros, direccion, ciudad, pais, actualizado
                FROM ubicaciones_usuarios
                WHERE usuario_id = %s 
                ORDER BY actualizado DESC 
                LIMIT 1""",
                (usuario_id,)
            )
            resultado = cursor.fetchone()
            
            if resultado:
                return {
                    'latitud': resultado[0],
                    'longitud': resultado[1],
                    'precision_metros': resultado[2],
                    'direccion': resultado[3],
                    'ciudad': resultado[4],
                    'pais': resultado[5],
                    'actualizado': resultado[6]
                }
            return None
        except Exception as e:
            print(f"Error obteniendo ubicación: {e}")
            return None
        finally:
            cursor.close()
            conn.close()