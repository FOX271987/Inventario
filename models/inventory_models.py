from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from models import db

class Producto(db.Model):
    __tablename__ = 'productos'

    ID_Producto = db.Column(db.Integer, primary_key=True)
    Codigo = db.Column(db.String(50), unique=True, nullable=False)
    Nombre = db.Column(db.String(100), nullable=False)
    Descripcion = db.Column(db.Text)
    Categoria = db.Column(db.String(50))
    Unidad = db.Column(db.String(20), nullable=False)
    Stock_Minimo = db.Column(db.Integer, default=0)
    Stock_Actual = db.Column(db.Integer, default=0)
    Activo = db.Column(db.Boolean, default=True)  # <- Este campo es crucial
    Fecha_Creacion = db.Column(db.DateTime, default=datetime.utcnow)

    movimientos = db.relationship('Movimiento', backref='producto', lazy=True)

    def to_dict(self):
        return {
            'ID_Producto': self.ID_Producto,
            'Codigo': self.Codigo,
            'Nombre': self.Nombre,
            'Descripcion': self.Descripcion,
            'Categoria': self.Categoria,
            'Unidad': self.Unidad,
            'Stock_Minimo': self.Stock_Minimo,
            'Stock_Actual': self.Stock_Actual,
            'Activo': self.Activo,
            'Fecha_Creacion': self.Fecha_Creacion.isoformat() if self.Fecha_Creacion else None
        }

class Proveedor(db.Model):
    __tablename__ = 'proveedores'

    ID_Proveedor = db.Column(db.Integer, primary_key=True)
    Nombre = db.Column(db.String(100), nullable=False)
    Telefono = db.Column(db.String(20))
    Contacto = db.Column(db.String(100))
    Email = db.Column(db.String(100))
    Activo = db.Column(db.Boolean, default=True)

    movimientos = db.relationship('Movimiento', backref='proveedor', lazy=True)

    def to_dict(self):
        return {
            'ID_Proveedor': self.ID_Proveedor,
            'Nombre': self.Nombre,
            'Telefono': self.Telefono,
            'Contacto': self.Contacto,
            'Email': self.Email,
            'Activo': self.Activo
        }

class Cliente(db.Model):
    __tablename__ = 'clientes'

    ID_Cliente = db.Column(db.Integer, primary_key=True)
    Nombre = db.Column(db.String(100), nullable=False)
    Telefono = db.Column(db.String(20))
    Contacto = db.Column(db.String(100))
    Email = db.Column(db.String(100))
    Activo = db.Column(db.Boolean, default=True)

    movimientos = db.relationship('Movimiento', backref='cliente', lazy=True)

    def to_dict(self):
        return {
            'ID_Cliente': self.ID_Cliente,
            'Nombre': self.Nombre,
            'Telefono': self.Telefono,
            'Contacto': self.Contacto,
            'Email': self.Email,
            'Activo': self.Activo
        }

class Movimiento(db.Model):
    __tablename__ = 'movimientos'

    ID_Movimiento = db.Column(db.Integer, primary_key=True)
    Fecha = db.Column(db.DateTime, default=datetime.utcnow)
    Tipo = db.Column(db.Enum('Entrada', 'Salida'), nullable=False)
    ID_Producto = db.Column(db.Integer, db.ForeignKey('productos.ID_Producto'), nullable=False)
    Cantidad = db.Column(db.Integer, nullable=False)
    Referencia_Documento = db.Column(db.String(100))
    Responsable = db.Column(db.String(100), nullable=False)
    ID_Proveedor = db.Column(db.Integer, db.ForeignKey('proveedores.ID_Proveedor'))
    ID_Cliente = db.Column(db.Integer, db.ForeignKey('clientes.ID_Cliente'))

    def to_dict(self):
        return {
            'ID_Movimiento': self.ID_Movimiento,
            'Fecha': self.Fecha.isoformat() if self.Fecha else None,
            'Tipo': self.Tipo,
            'ID_Producto': self.ID_Producto,
            'Cantidad': self.Cantidad,
            'Referencia_Documento': self.Referencia_Documento,
            'Responsable': self.Responsable,
            'ID_Proveedor': self.ID_Proveedor,
            'ID_Cliente': self.ID_Cliente,
            'producto_nombre': self.producto.Nombre if self.producto else None,
            'proveedor_nombre': self.proveedor.Nombre if self.proveedor else None,
            'cliente_nombre': self.cliente.Nombre if self.cliente else None
        }