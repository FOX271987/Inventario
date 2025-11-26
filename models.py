from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from datetime import datetime

db = SQLAlchemy()

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(50), nullable=False)
    
    def __init__(self, nombre, email, password, rol):
        self.nombre = nombre
        self.email = email
        self.password = password
        self.rol = rol
    
    @classmethod
    def obtener_todos(cls):
        return cls.query.order_by(cls.id).all()
    
    @classmethod
    def obtener_con_filtros(cls, nombre=None, rol=None):
        query = cls.query
        
        if nombre:
            query = query.filter(cls.nombre.ilike(f'%{nombre}%'))
        
        if rol:
            query = query.filter(cls.rol == rol)
        
        return query.order_by(cls.id).all()
    
    @classmethod
    def crear(cls, nombre, email, password, rol):
        # Verificar si el email ya existe
        if cls.query.filter_by(email=email).first():
            raise ValueError("El email ya existe")
        
        usuario = cls(nombre=nombre, email=email, password=password, rol=rol)
        db.session.add(usuario)
        db.session.commit()
        return usuario.id
    
    @classmethod
    def actualizar(cls, id, nombre, email, rol):
        usuario = cls.query.get(id)
        if not usuario:
            raise ValueError("Usuario no encontrado")
        
        # Verificar si el email ya existe en otro usuario
        if cls.query.filter(cls.email == email, cls.id != id).first():
            raise ValueError("El email ya está registrado en otro usuario")
        
        usuario.nombre = nombre
        usuario.email = email
        usuario.rol = rol
        db.session.commit()
        return True
    
    @classmethod
    def eliminar(cls, id):
        usuario = cls.query.get(id)
        if not usuario:
            raise ValueError("Usuario no encontrado")
        
        db.session.delete(usuario)
        db.session.commit()
        return True
    
    @classmethod
    def email_existe(cls, email):
        return cls.query.filter_by(email=email).first() is not None
    
    @classmethod
    def obtener_por_id(cls, id):
        return cls.query.get(id)
    
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
    Activo = db.Column(db.Boolean, default=True)
    Fecha_Creacion = db.Column(db.DateTime, default=datetime.utcnow)

    #Relaciones
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

    #Relaciones
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

    #Relaciones
    movimientos = db.relationship('Movimiento', backref='cliente', lazy=True)

    def to_dict(self):
        return{
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
            'Fecha': self.Fecha,
            'Tipo': self.Tipo,
            'ID_Producto': self.ID_Producto,
            'Cantidad': self.Cantidad,
            'Referencia_Documento': self.Referencia_Documento,
            'Responsable': self.Responsable,
            'ID_Proveedor': self.ID_Proveedor,
            'ID_Cliente': self.ID_Cliente,
            'producto_nombre': self.producto.Nombre if self.producto else None,
            'proveedor_nombre': self.cliente.Nombre if self.proveedor else None,
            'cliente_nombre': self.cliente.Nombre if self.cliente else None
        }