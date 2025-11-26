# controllers/inventario_controller.py - VERSIÓN MEJORADA CON MANEJO SEGURO DE HILOS

from flask import request, jsonify, session
from models import db, Producto, Movimiento, Proveedor, Cliente
from sqlalchemy.exc import SQLAlchemyError
from utils.notifications import NotificacionesInventario
import threading

def ejecutar_notificacion_segura(func, *args):
    """Ejecutar notificación en un hilo con contexto de aplicación"""
    def notificacion_con_contexto():
        try:
            from app_simple import app
            with app.app_context():
                func(*args)
        except Exception as e:
            print(f"❌ Error en notificación en hilo: {e}")
    
    thread = threading.Thread(target=notificacion_con_contexto)
    thread.daemon = True
    thread.start()

class InventarioController:
    
    # ===== PERMISOS Y VALIDACIONES =====
    
    @staticmethod
    def _tiene_permiso(accion_requerida):
        """Validar permisos según el rol del usuario"""
        rol = session.get('user_rol', 'lector')
        
        permisos = {
            'lector': ['ver_productos', 'ver_reportes', 'ver_alertas'],
            'editor': ['ver_productos', 'ver_reportes', 'ver_alertas', 
                      'crear_productos', 'editar_descripcion', 'editar_categoria',
                      'registrar_entradas', 'registrar_salidas', 
                      'crear_clientes', 'crear_proveedores'],
            'admin': ['ver_productos', 'ver_reportes', 'ver_alertas',
                     'crear_productos', 'editar_descripcion', 'editar_categoria',
                     'editar_codigo', 'editar_nombre', 'editar_unidad',
                     'editar_stock', 'desactivar_productos', 'eliminar_productos',
                     'registrar_entradas', 'registrar_salidas',
                     'crear_clientes', 'crear_proveedores']
        }
        
        return accion_requerida in permisos.get(rol, [])
    
    @staticmethod
    def _validar_permiso_o_denegar(accion_requerida):
        """Validar permiso y retornar error si no tiene acceso"""
        if not InventarioController._tiene_permiso(accion_requerida):
            return jsonify({
                'error': f'No tienes permisos para {accion_requerida.replace("_", " ")}'
            }), 403
        return None
    
    # ===== ENDPOINTS DE PRODUCTOS =====
    
    @staticmethod
    def obtener_productos():
        """Obtener lista de productos - Permitido para todos los roles"""
        try:
            # Obtener parámetros de filtro
            estado = request.args.get('estado', 'activo')  # Por defecto solo activos
            
            if estado == 'activo':
                productos = Producto.query.filter_by(Activo=True).all()
            elif estado == 'inactivo':
                productos = Producto.query.filter_by(Activo=False).all()
            else:  # 'todos'
                productos = Producto.query.all()
                
            return jsonify([producto.to_dict() for producto in productos]), 200
        except SQLAlchemyError as e:
            return jsonify({'error': 'Error al obtener productos'}), 500
    
    @staticmethod
    def crear_producto():
        """Crear nuevo producto - Solo editores y admins"""
        # Validar permiso
        error_resp = InventarioController._validar_permiso_o_denegar('crear_productos')
        if error_resp:
            return error_resp
            
        try:
            data = request.get_json()
            
            # Validar campos requeridos
            required_fields = ['Codigo', 'Nombre', 'Unidad']
            for field in required_fields:
                if field not in data or not data[field]:
                    return jsonify({'error': f'El campo {field} es requerido'}), 400
            
            # Verificar si el código ya existe
            if Producto.query.filter_by(Codigo=data['Codigo']).first():
                return jsonify({'error': 'El código del producto ya existe'}), 400
            
            producto = Producto(
                Codigo=data['Codigo'],
                Nombre=data['Nombre'],
                Descripcion=data.get('Descripcion'),
                Categoria=data.get('Categoria'),
                Unidad=data['Unidad'],
                Stock_Minimo=data.get('Stock_Minimo', 0),
                Stock_Actual=data.get('Stock_Actual', 0)
            )
            
            db.session.add(producto)
            db.session.commit()
            
            # 🔔 ENVIAR NOTIFICACIÓN POR CORREO - NUEVO PRODUCTO
            producto_dict = producto.to_dict()
            usuario_creador = session.get('user_nombre', 'Usuario del sistema')
            
            # Enviar notificación en segundo plano con contexto seguro
            ejecutar_notificacion_segura(
                NotificacionesInventario.notificar_nuevo_producto,
                producto_dict, usuario_creador
            )
            
            return jsonify({
                'success': True,
                'producto': producto.to_dict(),
                'message': 'Producto creado exitosamente'
            }), 201
            
        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({'error': 'Error al crear producto'}), 500
    
    @staticmethod
    def actualizar_producto(producto_id):
        """Actualizar producto con validación de permisos por campo"""
        try:
            producto = Producto.query.get(producto_id)
            if not producto:
                return jsonify({'error': 'Producto no encontrado'}), 404
            
            data = request.get_json()
            
            # Validar campos y permisos específicos
            campos_actualizados = []
            
            # Campos que solo admin puede modificar
            campos_admin = ['Codigo', 'Nombre', 'Unidad', 'Stock_Actual']
            for campo in campos_admin:
                if campo in data and data[campo] != getattr(producto, campo):
                    if not InventarioController._tiene_permiso('editar_' + campo.lower()):
                        return jsonify({
                            'error': f'No tienes permisos para editar {campo.lower().replace("_", " ")}'
                        }), 403
                    setattr(producto, campo, data[campo])
                    campos_actualizados.append(campo)
            
            # Campos que editor puede modificar
            campos_editor = ['Descripcion', 'Categoria']
            for campo in campos_editor:
                if campo in data and data[campo] != getattr(producto, campo):
                    if not InventarioController._tiene_permiso('editar_' + campo.lower()):
                        return jsonify({
                            'error': f'No tienes permisos para editar {campo.lower()}'
                        }), 403
                    setattr(producto, campo, data[campo])
                    campos_actualizados.append(campo)
            
            # Campos generales
            if 'Stock_Minimo' in data:
                setattr(producto, 'Stock_Minimo', data['Stock_Minimo'])
                campos_actualizados.append('Stock_Minimo')
            
            if campos_actualizados:
                db.session.commit()
                return jsonify({
                    'success': True,
                    'producto': producto.to_dict(),
                    'campos_actualizados': campos_actualizados,
                    'message': 'Producto actualizado exitosamente'
                }), 200
            else:
                return jsonify({
                    'message': 'No se detectaron cambios'
                }), 200
                
        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({'error': 'Error al actualizar producto'}), 500
    
    @staticmethod
    def desactivar_producto(producto_id):
        """Desactivar producto - Solo admin"""
        error_resp = InventarioController._validar_permiso_o_denegar('desactivar_productos')
        if error_resp:
            return error_resp
            
        try:
            producto = Producto.query.get(producto_id)
            if not producto:
                return jsonify({'error': 'Producto no encontrado'}), 404
            
            # CORRECCIÓN: Cambiar Activo a False en lugar de eliminar
            producto.Activo = False
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Producto desactivado exitosamente'
            }), 200
            
        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({'error': 'Error al desactivar producto'}), 500
    
    @staticmethod
    def activar_producto(producto_id):
        """Activar producto - Solo admin"""
        error_resp = InventarioController._validar_permiso_o_denegar('desactivar_productos')  # Mismo permiso
        if error_resp:
            return error_resp
            
        try:
            producto = Producto.query.get(producto_id)
            if not producto:
                return jsonify({'error': 'Producto no encontrado'}), 404
            
            producto.Activo = True
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Producto activado exitosamente'
            }), 200
            
        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({'error': 'Error al activar producto'}), 500
    
    @staticmethod
    def eliminar_producto(producto_id):
        """Eliminar producto - Solo admin"""
        error_resp = InventarioController._validar_permiso_o_denegar('eliminar_productos')
        if error_resp:
            return error_resp
            
        try:
            producto = Producto.query.get(producto_id)
            if not producto:
                return jsonify({'error': 'Producto no encontrado'}), 404
            
            # Verificar si hay movimientos asociados
            movimientos = Movimiento.query.filter_by(ID_Producto=producto_id).first()
            if movimientos:
                return jsonify({
                    'error': 'No se puede eliminar el producto porque tiene movimientos asociados. Desactívalo en su lugar.'
                }), 400
            
            db.session.delete(producto)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Producto eliminado exitosamente'
            }), 200
            
        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({'error': 'Error al eliminar producto'}), 500
    
    # ===== MOVIMIENTOS DE INVENTARIO =====
    
    @staticmethod
    def registrar_entrada():
        """Registrar entrada de inventario - Editores y admins"""
        error_resp = InventarioController._validar_permiso_o_denegar('registrar_entradas')
        if error_resp:
            return error_resp
            
        try:
            data = request.get_json()
            
            required_fields = ['ID_Producto', 'Cantidad', 'Responsable']
            for field in required_fields:
                if field not in data or not data[field]:
                    return jsonify({'error': f'El campo {field} es requerido'}), 400
            
            producto = Producto.query.get(data['ID_Producto'])
            if not producto:
                return jsonify({'error': 'Producto no encontrado'}), 404
            
            # Guardar stock anterior para la notificación
            stock_anterior = producto.Stock_Actual
            
            movimiento = Movimiento(
                Tipo='Entrada',
                ID_Producto=data['ID_Producto'],
                Cantidad=data['Cantidad'],
                Referencia_Documento=data.get('Referencia_Documento'),
                Responsable=data['Responsable'],
                ID_Proveedor=data.get('ID_Proveedor')
            )
            
            # Actualizar stock
            producto.Stock_Actual += data['Cantidad']
            nuevo_stock = producto.Stock_Actual
            
            db.session.add(movimiento)
            db.session.commit()
            
            # 🔔 ENVIAR NOTIFICACIÓN POR CORREO - ENTRADA
            movimiento_dict = movimiento.to_dict()
            producto_dict = producto.to_dict()
            usuario_responsable = data['Responsable']
            
            # Enviar notificación en segundo plano con contexto seguro
            ejecutar_notificacion_segura(
                NotificacionesInventario.notificar_entrada_inventario,
                movimiento_dict, producto_dict, usuario_responsable, nuevo_stock
            )
            
            return jsonify({
                'success': True,
                'movimiento': movimiento.to_dict(),
                'nuevo_stock': nuevo_stock,
                'message': 'Entrada registrada exitosamente'
            }), 201
            
        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({'error': 'Error al registrar entrada'}), 500
    
    @staticmethod
    def registrar_salida():
        """Registrar salida de inventario - Editores y admins"""
        error_resp = InventarioController._validar_permiso_o_denegar('registrar_salidas')
        if error_resp:
            return error_resp
            
        try:
            data = request.get_json()
            
            required_fields = ['ID_Producto', 'Cantidad', 'Responsable']
            for field in required_fields:
                if field not in data or not data[field]:
                    return jsonify({'error': f'El campo {field} es requerido'}), 400
            
            producto = Producto.query.get(data['ID_Producto'])
            if not producto:
                return jsonify({'error': 'Producto no encontrado'}), 404
            
            if producto.Stock_Actual < data['Cantidad']:
                return jsonify({'error': 'Stock insuficiente'}), 400
            
            # Guardar stock anterior para la notificación
            stock_anterior = producto.Stock_Actual
            
            movimiento = Movimiento(
                Tipo='Salida',
                ID_Producto=data['ID_Producto'],
                Cantidad=data['Cantidad'],
                Referencia_Documento=data.get('Referencia_Documento'),
                Responsable=data['Responsable'],
                ID_Cliente=data.get('ID_Cliente')
            )
            
            # Actualizar stock
            producto.Stock_Actual -= data['Cantidad']
            nuevo_stock = producto.Stock_Actual
            
            db.session.add(movimiento)
            db.session.commit()
            
            # 🔔 ENVIAR NOTIFICACIÓN POR CORREO - SALIDA
            movimiento_dict = movimiento.to_dict()
            producto_dict = producto.to_dict()
            usuario_responsable = data['Responsable']
            
            # Verificar si el producto se agotó después de la salida
            producto_agotado = nuevo_stock == 0
            
            # Enviar notificación de salida en segundo plano con contexto seguro
            ejecutar_notificacion_segura(
                NotificacionesInventario.notificar_salida_inventario,
                movimiento_dict, producto_dict, usuario_responsable, nuevo_stock
            )
            
            # 🔔 NOTIFICACIÓN ADICIONAL SI EL PRODUCTO SE AGOTÓ
            if producto_agotado:
                ejecutar_notificacion_segura(
                    NotificacionesInventario.notificar_stock_agotado,
                    producto_dict
                )
            
            return jsonify({
                'success': True,
                'movimiento': movimiento.to_dict(),
                'nuevo_stock': nuevo_stock,
                'message': 'Salida registrada exitosamente'
            }), 201
            
        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({'error': 'Error al registrar salida'}), 500
    
    # ===== REPORTES Y ALERTAS =====
    
    @staticmethod
    def obtener_alertas_stock():
        """Obtener alertas de stock bajo - Permitido para todos los roles"""
        try:
            productos_bajo_stock = Producto.query.filter(
                Producto.Stock_Actual < Producto.Stock_Minimo,
                Producto.Activo == True
            ).all()
            
            alertas = []
            for producto in productos_bajo_stock:
                alertas.append({
                    **producto.to_dict(),
                    'diferencia': producto.Stock_Minimo - producto.Stock_Actual,
                    'alerta': 'Stock crítico' if producto.Stock_Actual == 0 else 'Stock bajo'
                })
            
            # 🔔 NOTIFICAR STOCK BAJO PERIÓDICAMENTE
            for producto in productos_bajo_stock:
                if producto.Stock_Actual == 0:
                    # Producto agotado - notificar inmediatamente
                    ejecutar_notificacion_segura(
                        NotificacionesInventario.notificar_stock_agotado,
                        producto.to_dict()
                    )
                elif producto.Stock_Actual < producto.Stock_Minimo:
                    # Stock bajo - notificar
                    ejecutar_notificacion_segura(
                        NotificacionesInventario.notificar_stock_bajo,
                        producto.to_dict()
                    )
            
            return jsonify(alertas), 200
            
        except SQLAlchemyError as e:
            return jsonify({'error': 'Error al obtener alertas'}), 500
    
    @staticmethod
    def obtener_movimientos():
        """Obtener historial de movimientos - Permitido para todos los roles"""
        try:
            # Obtener parámetros de filtro
            producto_id = request.args.get('producto_id', type=int)
            tipo = request.args.get('tipo')
            limit = request.args.get('limit', 50, type=int)
            
            query = Movimiento.query
            
            if producto_id:
                query = query.filter_by(ID_Producto=producto_id)
            if tipo:
                query = query.filter_by(Tipo=tipo)
            
            movimientos = query.order_by(Movimiento.Fecha.desc()).limit(limit).all()
            return jsonify([movimiento.to_dict() for movimiento in movimientos]), 200
        except SQLAlchemyError as e:
            return jsonify({'error': 'Error al obtener movimientos'}), 500
    
    # ===== PROVEEDORES =====
    
    @staticmethod
    def obtener_proveedores():
        """Obtener lista de proveedores - Permitido para todos los roles"""
        try:
            proveedores = Proveedor.query.filter_by(Activo=True).all()
            return jsonify([proveedor.to_dict() for proveedor in proveedores]), 200
        except SQLAlchemyError as e:
            return jsonify({'error': 'Error al obtener proveedores'}), 500
    
    @staticmethod
    def crear_proveedor():
        """Crear nuevo proveedor - Editores y admins"""
        error_resp = InventarioController._validar_permiso_o_denegar('crear_proveedores')
        if error_resp:
            return error_resp
            
        try:
            data = request.get_json()
            
            required_fields = ['Nombre']
            for field in required_fields:
                if field not in data or not data[field]:
                    return jsonify({'error': f'El campo {field} es requerido'}), 400
            
            proveedor = Proveedor(
                Nombre=data['Nombre'],
                Telefono=data.get('Telefono'),
                Contacto=data.get('Contacto'),
                Email=data.get('Email')
            )
            
            db.session.add(proveedor)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'proveedor': proveedor.to_dict(),
                'message': 'Proveedor creado exitosamente'
            }), 201
            
        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({'error': 'Error al crear proveedor'}), 500
    
    # ===== CLIENTES =====
    
    @staticmethod
    def obtener_clientes():
        """Obtener lista de clientes - Permitido para todos los roles"""
        try:
            clientes = Cliente.query.filter_by(Activo=True).all()
            return jsonify([cliente.to_dict() for cliente in clientes]), 200
        except SQLAlchemyError as e:
            return jsonify({'error': 'Error al obtener clientes'}), 500
    
    @staticmethod
    def crear_cliente():
        """Crear nuevo cliente - Editores y admins"""
        error_resp = InventarioController._validar_permiso_o_denegar('crear_clientes')
        if error_resp:
            return error_resp
            
        try:
            data = request.get_json()
            
            required_fields = ['Nombre']
            for field in required_fields:
                if field not in data or not data[field]:
                    return jsonify({'error': f'El campo {field} es requerido'}), 400
            
            cliente = Cliente(
                Nombre=data['Nombre'],
                Telefono=data.get('Telefono'),
                Contacto=data.get('Contacto'),
                Email=data.get('Email')
            )
            
            db.session.add(cliente)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'cliente': cliente.to_dict(),
                'message': 'Cliente creado exitosamente'
            }), 201
            
        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({'error': 'Error al crear cliente'}), 500