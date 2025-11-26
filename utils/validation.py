import re
import bcrypt

def encriptar_password(password):
    """Encriptar contraseña usando bcrypt"""
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

def verificar_password(password, hashed_password):
    """Verificar contraseña contra hash almacenado"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def validar_email(email):
    """Validar formato de email"""
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(patron, email) is not None

def validar_nombre(nombre):
    """Validar que el nombre solo contenga letras y espacios"""
    if not nombre or nombre.strip() == "":
        return False, "El nombre no puede estar vacío"
    
    patron = r'^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\.\-]+$'
    if not re.match(patron, nombre):
        return False, "El nombre solo puede contener letras y espacios"
    
    if re.search(r'\d', nombre):
        return False, "El nombre no puede contener números"
    
    if len(nombre.strip()) < 2:
        return False, "El nombre debe tener al menos 2 caracteres"
    
    if len(nombre.strip()) > 100:
        return False, "El nombre no puede exceder 100 caracteres"
    
    return True, ""

def validar_password(password):
    """Validar contraseña con reglas específicas"""
    if not password or password.strip() == "":
        return False, "La contraseña no puede estar vacía"
    
    if len(password) < 6:
        return False, "La contraseña debe tener al menos 6 caracteres"
    
    if len(password) > 50:
        return False, "La contraseña no puede exceder 50 caracteres"
    
    if password.strip() == "":
        return False, "La contraseña no puede contener solo espacios"
    
    return True, ""

def validar_texto_simple(texto, campo_nombre, longitud_min=2, longitud_max=100):
    """Validar texto simple sin caracteres especiales ni números"""
    if not texto or texto.strip() == "":
        return False, f"El campo {campo_nombre} no puede estar vacío"
    
    patron = r'^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\.\-\'\(\)]+$'
    if not re.match(patron, texto):
        return False, f"El campo {campo_nombre} solo puede contener letras y espacios"
    
    if re.search(r'\d', texto):
        return False, f"El campo {campo_nombre} no puede contener números"
    
    texto_limpio = texto.strip()
    if len(texto_limpio) < longitud_min:
        return False, f"El campo {campo_nombre} debe tener al menos {longitud_min} caracteres"
    
    if len(texto_limpio) > longitud_max:
        return False, f"El campo {campo_nombre} no puede exceder {longitud_max} caracteres"
    
    return True, ""