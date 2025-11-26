import os
import pg8000
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'seguridad'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'linux'),
    'port': int(os.getenv('DB_PORT', 5432))
}

def get_connection():
    """Obtener conexión a PostgreSQL"""
    try:
        conn = pg8000.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Error conectando a PostgreSQL: {e}")
        raise

def init_db():
    """Inicializar base de datos"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Crear tabla de usuarios si no existe
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(100) NOT NULL,
                email VARCHAR(150) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                rol VARCHAR(50) NOT NULL CHECK (rol IN ('admin', 'editor', 'lector'))
            )
        ''')
        
        # Intentar agregar columnas si no existen
        try:
            cursor.execute("ALTER TABLE usuarios ADD COLUMN sesion_activa BOOLEAN DEFAULT FALSE")
            print("Columna 'sesion_activa' agregada")
        except Exception as e:
            print(f"Columna 'sesion_activa' ya existe o no se pudo agregar: {e}")
            conn.rollback()
        
        try:
            cursor.execute("ALTER TABLE usuarios ADD COLUMN ultima_sesion TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            print("Columna 'ultima_sesion' agregada")
        except Exception as e:
            print(f"Columna 'ultima_sesion' ya existe o no se pudo agregar: {e}")
            conn.rollback()
        
        # Tablas adicionales
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
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ubicaciones_usuarios (
                id SERIAL PRIMARY KEY,
                usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
                latitud DECIMAL(10, 8) NOT NULL,
                longitud DECIMAL(11, 8) NOT NULL,
                precision_metros DECIMAL(8, 2),
                direccion TEXT,
                ciudad VARCHAR(100),
                pais VARCHAR(100),
                creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                actualizado TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ubicaciones_usuario_id ON ubicaciones_usuarios(usuario_id)')
        
        # Verificar si hay usuarios
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        if cursor.fetchone()[0] == 0:
            from utils.validation import encriptar_password
            password_encriptada = encriptar_password('admin123')
            cursor.execute(
                "INSERT INTO usuarios (nombre, email, password, rol, sesion_activa) VALUES (%s, %s, %s, %s, %s)",
                ('Administrador', 'admin@example.com', password_encriptada, 'admin', False)
            )
            print("Usuario administrador creado: admin@example.com / admin123")
        
        # Tablas de inventario
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS productos (
                ID_Producto SERIAL PRIMARY KEY,
                Codigo VARCHAR(50) UNIQUE NOT NULL,
                Nombre VARCHAR(100) NOT NULL,
                Descripcion TEXT,
                Categoria VARCHAR(50),
                Unidad VARCHAR(20) NOT NULL,
                Stock_Minimo INTEGER DEFAULT 0,
                Stock_Actual INTEGER DEFAULT 0,
                Activo BOOLEAN DEFAULT TRUE,
                Fecha_Creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS proveedores (
                ID_Proveedor SERIAL PRIMARY KEY,
                Nombre VARCHAR(100) NOT NULL,
                Telefono VARCHAR(20),
                Contacto VARCHAR(100),
                Email VARCHAR(100),
                Activo BOOLEAN DEFAULT TRUE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clientes (
                ID_Cliente SERIAL PRIMARY KEY,
                Nombre VARCHAR(100) NOT NULL,
                Telefono VARCHAR(20),
                Contacto VARCHAR(100),
                Email VARCHAR(100),
                Activo BOOLEAN DEFAULT TRUE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS movimientos (
                ID_Movimiento SERIAL PRIMARY KEY,
                Fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                Tipo VARCHAR(10) NOT NULL CHECK (Tipo IN ('Entrada', 'Salida')),
                ID_Producto INTEGER NOT NULL REFERENCES productos(ID_Producto),
                Cantidad INTEGER NOT NULL,
                Referencia_Documento VARCHAR(100),
                Responsable VARCHAR(100) NOT NULL,
                ID_Proveedor INTEGER REFERENCES proveedores(ID_Proveedor),
                ID_Cliente INTEGER REFERENCES clientes(ID_Cliente)
            )
        ''')
        
        # Crear índices
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_movimientos_producto ON movimientos(ID_Producto)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_movimientos_fecha ON movimientos(Fecha)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_productos_activos ON productos(Activo)')

        conn.commit()
        print("Base de datos inicializada correctamente")
    except Exception as e:
        conn.rollback()
        print(f"Error inicializando base de datos: {e}")
    finally:
        cursor.close()
        conn.close()

def limpiar_sesiones_expiradas():
    """Limpiar sesiones que llevan más de 24 horas activas"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE usuarios 
            SET sesion_activa = FALSE 
            WHERE sesion_activa = TRUE 
            AND ultima_sesion < NOW() - INTERVAL '24 hours'
        """)
        conn.commit()
        print(f"Sesiones expiradas limpiadas: {cursor.rowcount}")
    except Exception as e:
        print(f"Error limpiando sesiones expiradas: {e}")
    finally:
        cursor.close()
        conn.close()