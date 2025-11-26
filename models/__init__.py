from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user import Usuario
from .inventory_models import Producto, Movimiento, Proveedor, Cliente

__all__ = ['db', 'Usuario', 'Producto', 'Movimiento', 'Proveedor', 'Cliente']