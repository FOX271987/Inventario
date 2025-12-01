# api/inventory.py - VERSIÓN CON JWT INTEGRADO
from flask import Blueprint, request, jsonify
from auth.decorators import login_required, twofa_required, editor_required, admin_required, rol_requerido
from controllers.inventario_controller import InventarioController
from models import Movimiento

inventory_bp = Blueprint('inventory', __name__)

# ===== ENDPOINTS DE PRODUCTOS =====

@inventory_bp.route('/productos', methods=['GET'])
@login_required
@twofa_required
def api_inventario_productos_get():
    """Obtener lista de productos - Todos los roles"""
    return InventarioController.obtener_productos()

@inventory_bp.route('/productos', methods=['POST'])
@login_required
@twofa_required
@rol_requerido('admin', 'editor')
def api_inventario_productos_post():
    """Crear nuevo producto - Editores y Admins"""
    return InventarioController.crear_producto()

@inventory_bp.route('/productos/<int:producto_id>', methods=['GET'])
@login_required
@twofa_required
def api_inventario_producto_get(producto_id):
    """Obtener producto específico - Todos los roles"""
    from models import Producto
    producto = Producto.query.get(producto_id)
    if not producto:
        return jsonify({'error': 'Producto no encontrado'}), 404
    return jsonify(producto.to_dict()), 200

@inventory_bp.route('/productos/<int:producto_id>', methods=['PUT'])
@login_required
@twofa_required
@rol_requerido('admin', 'editor')
def api_inventario_productos_put(producto_id):
    """Actualizar producto - Editores y Admins"""
    return InventarioController.actualizar_producto(producto_id)

@inventory_bp.route('/productos/<int:producto_id>/desactivar', methods=['PUT'])
@login_required
@twofa_required
@admin_required
def api_inventario_productos_desactivar(producto_id):
    """Desactivar producto - Solo Admin"""
    return InventarioController.desactivar_producto(producto_id)

@inventory_bp.route('/productos/<int:producto_id>/activar', methods=['PUT'])
@login_required
@twofa_required
@admin_required
def api_inventario_productos_activar(producto_id):
    """Activar producto - Solo Admin"""
    return InventarioController.activar_producto(producto_id)

@inventory_bp.route('/productos/<int:producto_id>', methods=['DELETE'])
@login_required
@twofa_required
@admin_required
def api_inventario_productos_delete(producto_id):
    """Eliminar producto - Solo Admin"""
    return InventarioController.eliminar_producto(producto_id)

# ===== ENDPOINTS DE MOVIMIENTOS =====

@inventory_bp.route('/entradas', methods=['POST'])
@login_required
@twofa_required
@rol_requerido('admin', 'editor')
def api_inventario_entradas():
    """Registrar entrada de inventario - Editores y Admins"""
    return InventarioController.registrar_entrada()

@inventory_bp.route('/salidas', methods=['POST'])
@login_required
@twofa_required
@rol_requerido('admin', 'editor')
def api_inventario_salidas():
    """Registrar salida de inventario - Editores y Admins"""
    return InventarioController.registrar_salida()

@inventory_bp.route('/movimientos', methods=['GET'])
@login_required
@twofa_required
def api_inventario_movimientos():
    """Obtener historial de movimientos - Todos los roles"""
    return InventarioController.obtener_movimientos()

# ===== ENDPOINTS DE ALERTAS =====

@inventory_bp.route('/alertas', methods=['GET'])
@login_required
@twofa_required
def api_inventario_alertas():
    """Obtener alertas de stock bajo - Todos los roles"""
    return InventarioController.obtener_alertas_stock()

# ===== ENDPOINTS DE PROVEEDORES =====

@inventory_bp.route('/proveedores', methods=['GET'])
@login_required
@twofa_required
def api_inventario_proveedores_get():
    """Obtener lista de proveedores - Todos los roles"""
    return InventarioController.obtener_proveedores()

@inventory_bp.route('/proveedores', methods=['POST'])
@login_required
@twofa_required
@rol_requerido('admin', 'editor')
def api_inventario_proveedores_post():
    """Crear nuevo proveedor - Editores y Admins"""
    return InventarioController.crear_proveedor()

# ===== ENDPOINTS DE CLIENTES =====

@inventory_bp.route('/clientes', methods=['GET'])
@login_required
@twofa_required
def api_inventario_clientes_get():
    """Obtener lista de clientes - Todos los roles"""
    return InventarioController.obtener_clientes()

@inventory_bp.route('/clientes', methods=['POST'])
@login_required
@twofa_required
@rol_requerido('admin', 'editor')
def api_inventario_clientes_post():
    """Crear nuevo cliente - Editores y Admins"""
    return InventarioController.crear_cliente()

# ===== ENDPOINTS DE REPORTES =====

@inventory_bp.route('/reportes/stock-bajo', methods=['GET'])
@login_required
@twofa_required
def api_inventario_reportes_stock_bajo():
    """Reporte de stock bajo - Todos los roles"""
    return InventarioController.obtener_alertas_stock()

@inventory_bp.route('/reportes/movimientos-detallados', methods=['GET'])
@login_required
@twofa_required
def api_inventario_reportes_movimientos_detallados():
    """Reporte detallado de movimientos - Todos los roles"""
    try:
        # Parámetros para reporte detallado
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        producto_id = request.args.get('producto_id', type=int)
        tipo = request.args.get('tipo')  # 'Entrada' o 'Salida'
        
        query = Movimiento.query
        
        if fecha_inicio:
            query = query.filter(Movimiento.Fecha >= fecha_inicio)
        if fecha_fin:
            query = query.filter(Movimiento.Fecha <= fecha_fin)
        if producto_id:
            query = query.filter_by(ID_Producto=producto_id)
        if tipo and tipo in ['Entrada', 'Salida']:
            query = query.filter_by(Tipo=tipo)
        
        movimientos = query.order_by(Movimiento.Fecha.desc()).all()
        
        # Calcular resumen
        total_entradas = sum(m.Cantidad for m in movimientos if m.Tipo == 'Entrada')
        total_salidas = sum(m.Cantidad for m in movimientos if m.Tipo == 'Salida')
        
        return jsonify({
            'movimientos': [movimiento.to_dict() for movimiento in movimientos],
            'resumen': {
                'total_entradas': total_entradas,
                'total_salidas': total_salidas,
                'balance': total_entradas - total_salidas,
                'total_movimientos': len(movimientos)
            },
            'filtros_aplicados': {
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin,
                'producto_id': producto_id,
                'tipo': tipo
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al generar reporte: {str(e)}'}), 500

@inventory_bp.route('/reportes/resumen', methods=['GET'])
@login_required
@twofa_required
def api_inventario_reportes_resumen():
    """Resumen general del inventario - Todos los roles"""
    try:
        from models import Producto
        
        productos = Producto.query.filter_by(Activo=True).all()
        
        total_productos = len(productos)
        productos_stock_bajo = sum(1 for p in productos if p.Stock_Actual <= p.Stock_Minimo)
        productos_sin_stock = sum(1 for p in productos if p.Stock_Actual == 0)
        valor_total_unidades = sum(p.Stock_Actual for p in productos)
        
        return jsonify({
            'resumen': {
                'total_productos_activos': total_productos,
                'productos_stock_bajo': productos_stock_bajo,
                'productos_sin_stock': productos_sin_stock,
                'total_unidades_inventario': valor_total_unidades
            },
            'alertas': {
                'criticas': productos_sin_stock,
                'advertencias': productos_stock_bajo - productos_sin_stock
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al generar resumen: {str(e)}'}), 500