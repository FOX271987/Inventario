from flask import Blueprint, jsonify, request, session
from auth.decorators import login_required, twofa_required
from models.user import Usuario
from utils.location_services import obtener_servicios_reales_completos, obtener_servicios_simulados_completos, calcular_distancia
from auth.utils import obtener_direccion_desde_coordenadas, verificar_conexion
import random
import math
from datetime import datetime

location_bp = Blueprint('location', __name__)

@location_bp.route('/ubicacion')
@login_required
@twofa_required
def ubicacion():
    return render_template('ubicacion.html', user_rol=session.get('user_rol', 'lector'))

# ============================================================================
# ENDPOINTS DE SERVICIOS CERCANOS
# ============================================================================

@location_bp.route('/api/location/services', methods=['GET'])
@login_required
@twofa_required
def api_get_nearby_services():
    """Endpoint para obtener servicios cercanos"""
    try:
        lat = request.args.get('lat', type=float)
        lng = request.args.get('lng', type=float)
        
        if lat is None or lng is None:
            lat = 20.6597
            lng = -103.3496
        
        radius_input = request.args.get('radius', type=int, default=5)
        max_results = int(request.args.get('limit', 50))
        
        if radius_input > 100:
            radius_km = radius_input / 1000
        else:
            radius_km = radius_input
        
        radius_km = min(radius_km, 50)
        max_results = min(max_results, 100)
        radius_meters = int(radius_km * 1000)
        
        lat = float(str(lat)) if not isinstance(lat, float) else lat
        lng = float(str(lng)) if not isinstance(lng, float) else lng
        
        tiene_conexion = verificar_conexion()
        
        servicios = []
        fuente_datos = ""
        
        if tiene_conexion:
            servicios_reales = obtener_servicios_reales_completos(lat, lng, radius_meters, max_results)
            if servicios_reales:
                servicios = servicios_reales
                fuente_datos = "openstreetmap"
            else:
                servicios = obtener_servicios_simulados_completos(lat, lng, radius_km, max_results)
                fuente_datos = "simulacion (fallback)"
        else:
            servicios = obtener_servicios_simulados_completos(lat, lng, radius_km, max_results)
            fuente_datos = "simulacion (offline)"
        
        categorias_servicios = {}
        for servicio in servicios:
            categoria = servicio['categoria']
            if categoria not in categorias_servicios:
                categorias_servicios[categoria] = []
            categorias_servicios[categoria].append(servicio)
        
        return jsonify({
            'success': True,
            'servicios': servicios,
            'categorias': categorias_servicios,
            'metadata': {
                'total_resultados': len(servicios),
                'radio_solicitado_km': radius_km,
                'radio_utilizado_metros': radius_meters,
                'limite_resultados': max_results,
                'fuente_datos': fuente_datos,
                'modo_conexion': 'online' if tiene_conexion else 'offline',
                'total_categorias': len(categorias_servicios),
                'categorias_disponibles': list(categorias_servicios.keys()),
                'coordenadas_busqueda': {
                    'latitud': lat,
                    'longitud': lng
                }
            },
            'message': f'Se encontraron {len(servicios)} servicios en un radio de {radius_km} km'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al obtener servicios: {str(e)}'}), 500

# ============================================================================
# ENDPOINTS DE ACTUALIZACIÓN DE UBICACIÓN
# ============================================================================

@location_bp.route('/api/location/', methods=['POST'])
@login_required
@twofa_required
def api_update_user_location():
    """Endpoint principal para actualizar ubicación del usuario (usado por ubicacion.html)"""
    try:
        data = request.get_json()
        if not data or 'latitud' not in data or 'longitud' not in data:
            return jsonify({'error': 'Datos de ubicación requeridos'}), 400
        
        latitud = data['latitud']
        longitud = data['longitud']
        precision = data.get('precision')
        es_offline = data.get('offline', False)
        
        if es_offline:
            info_direccion = data.get('direccion_cache', {})
        else:
            info_direccion = obtener_direccion_desde_coordenadas(latitud, longitud)
        
        exito = Usuario.guardar_ubicacion(
            session['user_id'],
            latitud,
            longitud,
            precision,
            info_direccion.get('direccion'),
            info_direccion.get('ciudad'),
            info_direccion.get('pais')
        )
        
        if exito:
            session['user_ubicacion'] = {
                'latitud': latitud,
                'longitud': longitud,
                'precision': precision,
                'direccion': info_direccion.get('direccion'),
                'offline': es_offline
            }
            
            mensaje = 'Ubicación actualizada' + (' (modo offline)' if es_offline else '')
            return jsonify({'success': True, 'message': mensaje, 'offline': es_offline})
        else:
            return jsonify({'success': False, 'message': 'Error al guardar ubicación'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@location_bp.route('/api/location/actualizar-ubicacion', methods=['POST'])
@login_required
@twofa_required
def api_actualizar_ubicacion():
    """Endpoint para actualizar ubicación desde el perfil de usuario"""
    try:
        data = request.get_json()
        if not data or 'latitud' not in data or 'longitud' not in data:
            return jsonify({'error': 'Datos de ubicación requeridos'}), 400
        
        latitud = data['latitud']
        longitud = data['longitud']
        precision = data.get('precision')
        
        # Obtener información de dirección
        info_direccion = obtener_direccion_desde_coordenadas(latitud, longitud)
        
        exito = Usuario.guardar_ubicacion(
            session['user_id'],
            latitud,
            longitud,
            precision,
            info_direccion.get('direccion') if info_direccion else None,
            info_direccion.get('ciudad') if info_direccion else None,
            info_direccion.get('pais') if info_direccion else None
        )
        
        if exito:
            # Actualizar sesión
            session['user_ubicacion'] = {
                'latitud': latitud,
                'longitud': longitud,
                'precision': precision,
                'direccion': info_direccion.get('direccion') if info_direccion else None,
                'ciudad': info_direccion.get('ciudad') if info_direccion else None,
                'pais': info_direccion.get('pais') if info_direccion else None
            }
            
            return jsonify({
                'success': True,
                'message': 'Ubicación actualizada correctamente',
                'ubicacion': session['user_ubicacion']
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Error al guardar ubicación'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

# ============================================================================
# ENDPOINTS DE CONSULTA DE UBICACIÓN
# ============================================================================

@location_bp.route('/api/location/profile/<int:user_id>', methods=['GET'])
@login_required
@twofa_required
def api_get_user_location(user_id):
    """Endpoint para obtener la última ubicación registrada de un usuario específico"""
    try:
        if session['user_id'] != user_id and session['user_rol'] != 'admin':
            return jsonify({'error': 'No tienes permisos para ver esta ubicación'}), 403
        
        ultima_ubicacion = Usuario.obtener_ultima_ubicacion(user_id)
        usuario = Usuario.obtener_por_id(user_id)
        
        if not usuario:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        response_data = {
            'success': True,
            'user_id': user_id,
            'user_nombre': usuario.nombre,
            'user_email': usuario.email
        }
        
        if ultima_ubicacion:
            response_data['ultima_ubicacion'] = ultima_ubicacion
            response_data['message'] = 'Ubicación encontrada'
        else:
            response_data['message'] = 'No hay ubicación registrada para este usuario'
        
        return jsonify(response_data), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al obtener ubicación: {str(e)}'}), 500

@location_bp.route('/api/location/current', methods=['GET'])
@login_required
@twofa_required
def api_get_current_location():
    """Endpoint para obtener la ubicación actual del usuario desde la sesión"""
    try:
        ubicacion_actual = session.get('user_ubicacion')
        ultima_ubicacion = Usuario.obtener_ultima_ubicacion(session['user_id'])
        
        response_data = {
            'success': True,
            'user_id': session['user_id']
        }
        
        if ubicacion_actual:
            response_data['ubicacion_actual'] = ubicacion_actual
            response_data['fuente'] = 'sesion'
        elif ultima_ubicacion:
            response_data['ubicacion_actual'] = ultima_ubicacion
            response_data['fuente'] = 'base_datos'
        else:
            response_data['message'] = 'No hay ubicación disponible'
        
        return jsonify(response_data), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al obtener ubicación actual: {str(e)}'}), 500

@location_bp.route('/api/location/ubicacion-usuario', methods=['GET'])
@login_required
@twofa_required
def api_obtener_ubicacion_usuario():
    """Endpoint para obtener la ubicación del usuario actual (simplificado)"""
    try:
        user_id = session['user_id']
        ultima_ubicacion = Usuario.obtener_ultima_ubicacion(user_id)
        
        response_data = {
            'success': True,
            'user_id': user_id,
            'user_nombre': session.get('user_nombre'),
            'user_email': session.get('user_email')
        }
        
        if ultima_ubicacion:
            response_data['ubicacion'] = ultima_ubicacion
            response_data['message'] = 'Ubicación encontrada'
        else:
            response_data['message'] = 'No hay ubicación registrada'
        
        return jsonify(response_data), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al obtener ubicación: {str(e)}'}), 500
    
@location_bp.route('/health', methods=['GET'])
def health_check():
    """Endpoint de salud para la API de ubicación"""
    return jsonify({
        'status': 'healthy',
        'service': 'location_api',
        'timestamp': datetime.now().isoformat()
    })

# ============================================================================
# FUNCIÓN AUXILIAR
# ============================================================================

def render_template(template, **kwargs):
    from flask import render_template as flask_render_template
    return flask_render_template(template, **kwargs)