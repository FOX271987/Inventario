# swagger_routes.py - ACTUALIZADO CON JWT REAL Y PRODUCTOS
from flask_restx import Resource
from flask import request, jsonify, session
from swagger_config import (
    api, token_required, generar_token,
    user_create_model, login_model,
    producto_create_model, producto_update_model,
    movimiento_entrada_model, movimiento_salida_model
)
from models import Usuario, Producto
from controllers.inventario_controller import InventarioController

# Crear namespaces
ns_auth = api.namespace('auth', description='Autenticación')
ns_productos = api.namespace('productos', description='Gestión de productos')
ns_movimientos = api.namespace('movimientos', description='Movimientos de inventario')

# ========== AUTENTICACIÓN ==========

@ns_auth.route('/login')
class Login(Resource):
    @api.expect(login_model)
    def post(self):
        """Iniciar sesión y obtener token JWT"""
        data = request.get_json()
        
        if not data or 'email' not in data or 'password' not in data:
            return {'message': 'Email y contraseña son requeridos'}, 400
        
        usuario = Usuario.query.filter_by(email=data['email']).first()
        
        if not usuario or usuario.password != data['password']:
            return {'message': 'Email o contraseña incorrectos'}, 401
        
        token = generar_token(
            user_id=usuario.id,
            email=usuario.email,
            nombre=usuario.nombre,
            rol=usuario.rol
        )
        
        session['user_id'] = usuario.id
        session['user_nombre'] = usuario.nombre
        session['user_email'] = usuario.email
        session['user_rol'] = usuario.rol
        
        return {
            'message': 'Login exitoso',
            'token': token,
            'user': {
                'id': usuario.id,
                'nombre': usuario.nombre,
                'email': usuario.email,
                'rol': usuario.rol
            }
        }, 200

@ns_auth.route('/verify-token')
class VerifyToken(Resource):
    @api.doc(security='Bearer Auth')
    @token_required
    def get(self):
        """Verificar si el token JWT es válido"""
        return {'valid': True, 'user': request.user}, 200

@ns_auth.route('/logout')
class Logout(Resource):
    def post(self):
        """Cerrar sesión"""
        session.clear()
        return {'message': 'Sesión cerrada exitosamente'}, 200

@ns_auth.route('/register')
class Register(Resource):
    @api.expect(user_create_model)
    def post(self):
        """Registrar nuevo usuario"""
        data = request.get_json()
        
        try:
            usuario_id = Usuario.crear(
                data['nombre'],
                data['email'],
                data['password'],
                data.get('rol', 'lector')
            )
            return {'message': 'Usuario creado exitosamente', 'user_id': usuario_id}, 201
        except ValueError as e:
            return {'message': str(e)}, 400

# ========== PRODUCTOS ==========

@ns_productos.route('/')
class ProductoList(Resource):
    @api.doc(security='Bearer Auth')
    @token_required
    def get(self):
        """Obtener lista de productos"""
        return InventarioController.obtener_productos()
    
    @api.doc(security='Bearer Auth')
    @api.expect(producto_create_model)
    @token_required
    def post(self):
        """Crear nuevo producto"""
        session['user_id'] = request.user['user_id']
        session['user_nombre'] = request.user['nombre']
        session['user_rol'] = request.user['rol']
        return InventarioController.crear_producto()

@ns_productos.route('/<int:producto_id>')
class ProductoDetail(Resource):
    @api.doc(security='Bearer Auth')
    @token_required
    def get(self, producto_id):
        """Obtener producto específico"""
        producto = Producto.query.get(producto_id)
        if not producto:
            return {'error': 'Producto no encontrado'}, 404
        return producto.to_dict(), 200
    
    @api.doc(security='Bearer Auth')
    @api.expect(producto_update_model)
    @token_required
    def put(self, producto_id):
        """Actualizar producto"""
        session['user_id'] = request.user['user_id']
        session['user_nombre'] = request.user['nombre']
        session['user_rol'] = request.user['rol']
        return InventarioController.actualizar_producto(producto_id)
    
    @api.doc(security='Bearer Auth')
    @token_required
    def delete(self, producto_id):
        """Eliminar producto"""
        session['user_id'] = request.user['user_id']
        session['user_rol'] = request.user['rol']
        return InventarioController.eliminar_producto(producto_id)

@ns_productos.route('/<int:producto_id>/desactivar')
class ProductoDesactivar(Resource):
    @api.doc(security='Bearer Auth')
    @token_required
    def post(self, producto_id):
        """Desactivar producto"""
        session['user_rol'] = request.user['rol']
        return InventarioController.desactivar_producto(producto_id)

@ns_productos.route('/<int:producto_id>/activar')
class ProductoActivar(Resource):
    @api.doc(security='Bearer Auth')
    @token_required
    def post(self, producto_id):
        """Activar producto"""
        session['user_rol'] = request.user['rol']
        return InventarioController.activar_producto(producto_id)

@ns_productos.route('/alertas')
class ProductoAlertas(Resource):
    @api.doc(security='Bearer Auth')
    @token_required
    def get(self):
        """Obtener alertas de stock bajo"""
        return InventarioController.obtener_alertas_stock()

# ========== MOVIMIENTOS ==========

@ns_movimientos.route('/entrada')
class MovimientoEntrada(Resource):
    @api.doc(security='Bearer Auth')
    @api.expect(movimiento_entrada_model)
    @token_required
    def post(self):
        """Registrar entrada de inventario"""
        session['user_rol'] = request.user['rol']
        return InventarioController.registrar_entrada()

@ns_movimientos.route('/salida')
class MovimientoSalida(Resource):
    @api.doc(security='Bearer Auth')
    @api.expect(movimiento_salida_model)
    @token_required
    def post(self):
        """Registrar salida de inventario"""
        session['user_rol'] = request.user['rol']
        return InventarioController.registrar_salida()

@ns_movimientos.route('/historial')
class MovimientoHistorial(Resource):
    @api.doc(security='Bearer Auth')
    @token_required
    def get(self):
        """Obtener historial de movimientos"""
        return InventarioController.obtener_movimientos()