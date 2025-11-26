import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Configuración de PostgreSQL con pg8000
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_NAME = os.getenv('DB_NAME', 'seguridad')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'linux')
    DB_PORT = os.getenv('DB_PORT', '5432')
    
    # Cadena de conexión para PostgreSQL con pg8000
    SQLALCHEMY_DATABASE_URI = f'postgresql+pg8000://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    
    # Configuración de Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'mi-clave-secreta')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'