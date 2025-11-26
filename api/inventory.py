from flask import Blueprint, request, jsonify
from auth.decorators import login_required, twofa_required
from controllers.inventario_controller import InventarioController
from models import Movimiento

inventory_bp = Blueprint('inventory', __name__)

# ===== ENDPOINTS EXISTENTES =====

@inventory_bp.route('/productos', methods=['GET'])
@login_required
@twofa_required
def api_inventario_productos_get():
    """Obtener lista de productos - Todos los roles"""
    return InventarioController.obtener_productos()

@inventory_bp.route('/productos', methods=['POST'])
@login_required
@twofa_required
def api_inventario_productos_post():
    """Crear nuevo producto - Editores y Admins"""
    return InventarioController.crear_producto()

@inventory_bp.route('/productos/<int:producto_id>', methods=['PUT'])
@login_required
@twofa_required
def api_inventario_productos_put(producto_id):
    """Actualizar producto - Permisos específicos por campo"""
    return InventarioController.actualizar_producto(producto_id)

@inventory_bp.route('/productos/<int:producto_id>/desactivar', methods=['PUT'])
@login_required
@twofa_required
def api_inventario_productos_desactivar(producto_id):
    """Desactivar producto - Solo Admin"""
    return InventarioController.desactivar_producto(producto_id)

@inventory_bp.route('/productos/<int:producto_id>/activar', methods=['PUT'])
@login_required
@twofa_required
def api_inventario_productos_activar(producto_id):
    """Activar producto - Solo Admin"""
    return InventarioController.activar_producto(producto_id)

@inventory_bp.route('/productos/<int:producto_id>', methods=['DELETE'])
@login_required
@twofa_required
def api_inventario_productos_delete(producto_id):
    """Eliminar producto - Solo Admin"""
    return InventarioController.eliminar_producto(producto_id)

@inventory_bp.route('/entradas', methods=['POST'])
@login_required
@twofa_required
def api_inventario_entradas():
    """Registrar entrada de inventario - Editores y Admins"""
    return InventarioController.registrar_entrada()

@inventory_bp.route('/salidas', methods=['POST'])
@login_required
@twofa_required
def api_inventario_salidas():
    """Registrar salida de inventario - Editores y Admins"""
    return InventarioController.registrar_salida()

@inventory_bp.route('/alertas', methods=['GET'])
@login_required
@twofa_required
def api_inventario_alertas():
    """Obtener alertas de stock bajo - Todos los roles"""
    return InventarioController.obtener_alertas_stock()

@inventory_bp.route('/movimientos', methods=['GET'])
@login_required
@twofa_required
def api_inventario_movimientos():
    """Obtener historial de movimientos - Todos los roles"""
    return InventarioController.obtener_movimientos()

@inventory_bp.route('/proveedores', methods=['GET'])
@login_required
@twofa_required
def api_inventario_proveedores_get():
    """Obtener lista de proveedores - Todos los roles"""
    return InventarioController.obtener_proveedores()

@inventory_bp.route('/proveedores', methods=['POST'])
@login_required
@twofa_required
def api_inventario_proveedores_post():
    """Crear nuevo proveedor - Editores y Admins"""
    return InventarioController.crear_proveedor()

@inventory_bp.route('/clientes', methods=['GET'])
@login_required
@twofa_required
def api_inventario_clientes_get():
    """Obtener lista de clientes - Todos los roles"""
    return InventarioController.obtener_clientes()

@inventory_bp.route('/clientes', methods=['POST'])
@login_required
@twofa_required
def api_inventario_clientes_post():
    """Crear nuevo cliente - Editores y Admins"""
    return InventarioController.crear_cliente()

# ===== NUEVOS ENDPOINTS PARA REPORTES =====

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
        
        query = Movimiento.query
        
        if fecha_inicio:
            query = query.filter(Movimiento.Fecha >= fecha_inicio)
        if fecha_fin:
            query = query.filter(Movimiento.Fecha <= fecha_fin)
        if producto_id:
            query = query.filter_by(ID_Producto=producto_id)
        
        movimientos = query.order_by(Movimiento.Fecha.desc()).all()
        
        # Calcular resumen
        total_entradas = sum(m.Cantidad for m in movimientos if m.Tipo == 'Entrada')
        total_salidas = sum(m.Cantidad for m in movimientos if m.Tipo == 'Salida')
        
        return jsonify({
            'movimientos': [movimiento.to_dict() for movimiento in movimientos],
            'resumen': {
                'total_entradas': total_entradas,
                'total_salidas': total_salidas,
                'total_movimientos': len(movimientos)
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al generar reporte: {str(e)}'}), 500