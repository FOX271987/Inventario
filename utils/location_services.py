import requests
import random
import math
from math import radians, sin, cos, sqrt, atan2

def calcular_distancia(lat1, lng1, lat2, lng2):
    """Calcular distancia en metros entre dos puntos"""
    try:
        lat1 = float(lat1) if not isinstance(lat1, float) else lat1
        lng1 = float(lng1) if not isinstance(lng1, float) else lng1
        lat2 = float(lat2) if not isinstance(lat2, float) else lat2
        lng2 = float(lng2) if not isinstance(lng2, float) else lng2
    except:
        return 1000
    
    R = 6371000
    
    lat1_rad = radians(lat1)
    lng1_rad = radians(lng1)
    lat2_rad = radians(lat2)
    lng2_rad = radians(lng2)
    
    dlat = lat2_rad - lat1_rad
    dlng = lng2_rad - lng1_rad
    
    a = sin(dlat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlng/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c

def obtener_servicios_reales_completos(lat, lng, radius_meters=5000, max_results=100):
    """Obtener servicios reales de OpenStreetMap con todas las categorías"""
    try:
        overpass_query = f"""
        [out:json][timeout:30];
        (
            node(around:{radius_meters},{lat},{lng})[amenity];
            way(around:{radius_meters},{lat},{lng})[amenity];
            relation(around:{radius_meters},{lat},{lng})[amenity];
            
            node(around:{radius_meters},{lat},{lng})[shop];
            way(around:{radius_meters},{lat},{lng})[shop];
            relation(around:{radius_meters},{lat},{lng})[shop];
            
            node(around:{radius_meters},{lat},{lng})[tourism];
            way(around:{radius_meters},{lat},{lng})[tourism];
            relation(around:{radius_meters},{lat},{lng})[tourism];
            
            node(around:{radius_meters},{lat},{lng})[office];
            way(around:{radius_meters},{lat},{lng})[office];
            relation(around:{radius_meters},{lat},{lng})[office];
            
            node(around:{radius_meters},{lat},{lng})[public_transport];
            way(around:{radius_meters},{lat},{lng})[public_transport];
            relation(around:{radius_meters},{lat},{lng})[public_transport];
            
            node(around:{radius_meters},{lat},{lng})[leisure];
            way(around:{radius_meters},{lat},{lng})[leisure];
            relation(around:{radius_meters},{lat},{lng})[leisure];
            
            node(around:{radius_meters},{lat},{lng})[amenity=bank];
            node(around:{radius_meters},{lat},{lng})[amenity=atm];
        );
        out center {max_results};
        """
        
        url = "https://overpass-api.de/api/interpreter"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'SistemaSeguridadApp/1.0'
        }
        
        response = requests.post(url, data=f"data={overpass_query}", headers=headers, timeout=30)
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        servicios = []
        
        for elemento in data.get('elements', []):
            tags = elemento.get('tags', {})
            nombre = tags.get('name', 'Sin nombre')
            
            if nombre == 'Sin nombre':
                continue
            
            if elemento['type'] == 'node':
                lat_serv = elemento.get('lat')
                lon_serv = elemento.get('lon')
            else:
                if 'center' in elemento:
                    lat_serv = elemento['center']['lat']
                    lon_serv = elemento['center']['lon']
                else:
                    continue
            
            distancia_metros = calcular_distancia(lat, lng, lat_serv, lon_serv)
            distancia_km = distancia_metros / 1000
            
            amenity = tags.get('amenity', '')
            shop = tags.get('shop', '')
            tourism = tags.get('tourism', '')
            office = tags.get('office', '')
            leisure = tags.get('leisure', '')
            
            categoria_base = amenity or shop or tourism or office or leisure or 'otro'
            
            mapeo_categorias = {
                'restaurant': 'Restaurante', 'cafe': 'Cafetería', 'bar': 'Bar', 
                'pub': 'Pub', 'fast_food': 'Comida Rápida', 'food_court': 'Plaza de Comida',
                'hospital': 'Hospital', 'clinic': 'Clínica', 'doctors': 'Médico',
                'dentist': 'Dentista', 'pharmacy': 'Farmacia', 'optometrist': 'Óptica',
                'school': 'Escuela', 'university': 'Universidad', 'college': 'Colegio',
                'kindergarten': 'Guardería', 'library': 'Biblioteca',
                'bank': 'Banco', 'atm': 'Cajero', 'money_transfer': 'Transferencias',
                'fuel': 'Gasolinera', 'parking': 'Estacionamiento', 'bus_station': 'Autobuses',
                'taxi': 'Taxi', 'car_rental': 'Renta de Autos', 'bicycle_rental': 'Renta de Bicicletas',
                'supermarket': 'Supermercado', 'mall': 'Centro Comercial', 'convenience': 'Tienda',
                'department_store': 'Tienda Departamental', 'clothes': 'Ropa', 'shoes': 'Zapatos',
                'electronics': 'Electrónicos', 'hardware': 'Ferretería',
                'post_office': 'Correos', 'police': 'Policía', 'fire_station': 'Bomberos',
                'courthouse': 'Tribunal', 'townhall': 'Gobierno', 'public_building': 'Edificio Público',
                'hotel': 'Hotel', 'motel': 'Motel', 'hostel': 'Hostal', 'guest_house': 'Casa de Huéspedes',
                'attraction': 'Atracción', 'museum': 'Museo', 'gallery': 'Galería',
                'cinema': 'Cine', 'theatre': 'Teatro', 'park': 'Parque', 'garden': 'Jardín',
                'sports_centre': 'Centro Deportivo', 'stadium': 'Estadio', 'swimming_pool': 'Alberca',
                'place_of_worship': 'Lugar de Culto', 'nightclub': 'Club Nocturno', 'marketplace': 'Mercado'
            }
            
            categoria_amigable = mapeo_categorias.get(categoria_base, categoria_base.title())
            
            servicios.append({
                'id': elemento['id'],
                'nombre': nombre,
                'categoria': categoria_amigable,
                'tipo_original': categoria_base,
                'distancia_metros': int(distancia_metros),
                'distancia_km': round(distancia_km, 2),
                'distancia_texto': f"{distancia_km:.1f} km",
                'latitud': float(lat_serv),
                'longitud': float(lon_serv),
                'direccion': tags.get('addr:street', 'Dirección no disponible'),
                'telefono': tags.get('phone', 'No disponible'),
                'horario': tags.get('opening_hours', 'No disponible'),
                'website': tags.get('website', ''),
                'fuente': 'openstreetmap'
            })
        
        servicios.sort(key=lambda x: x['distancia_metros'])
        return servicios[:max_results]
        
    except Exception as e:
        print(f"Error obteniendo servicios reales: {e}")
        return None

def obtener_servicios_simulados_completos(lat, lng, radius_km=5, max_results=50):
    """Generar servicios simulados completos para modo offline"""
    try:
        lat = float(lat) if not isinstance(lat, float) else lat
        lng = float(lng) if not isinstance(lng, float) else lng
    except:
        lat = 20.6597
        lng = -103.3496
    
    catalogo_servicios = [
        {
            'categoria': 'Restaurante',
            'nombres': ['Restaurante La Parrilla', 'Cafetería Central', 'Pizzería Italiana', 
                       'Mariscos Don José', 'Comida China Mandarin', 'Tacos El Güero'],
            'tipos': ['restaurant', 'cafe', 'fast_food']
        },
        {
            'categoria': 'Salud', 
            'nombres': ['Hospital General', 'Clínica Dental', 'Farmacia San José', 
                       'Laboratorio Clínico', 'Óptica Visual', 'Consultorio Médico'],
            'tipos': ['hospital', 'clinic', 'pharmacy', 'doctors', 'dentist']
        },
        {
            'categoria': 'Transporte',
            'nombres': ['Estación de Autobuses', 'Gasolinera PEMEX', 'Renta de Autos Express',
                       'Taller Mecánico', 'Lavado de Autos', 'Estacionamiento Central'],
            'tipos': ['bus_station', 'fuel', 'car_rental', 'car_wash', 'parking']
        },
        {
            'categoria': 'Comercio',
            'nombres': ['Supermercado Mega', 'Centro Comercial', 'Mercado Municipal',
                       'Tienda Departamental', 'Plaza Comercial', 'Mini Super'],
            'tipos': ['supermarket', 'mall', 'department_store', 'convenience']
        },
        {
            'categoria': 'Educación',
            'nombres': ['Escuela Primaria', 'Colegio Nacional', 'Universidad', 
                       'Biblioteca Pública', 'Guardería Infantil', 'Centro de Idiomas'],
            'tipos': ['school', 'university', 'library', 'kindergarten']
        },
        {
            'categoria': 'Servicios Públicos',
            'nombres': ['Oficina de Gobierno', 'Policía Municipal', 'Bomberos',
                       'Oficina Postal', 'Registro Civil', 'Tribunal'],
            'tipos': ['police', 'fire_station', 'post_office', 'townhall', 'courthouse']
        },
        {
            'categoria': 'Entretenimiento',
            'nombres': ['Cine Multiplex', 'Parque Central', 'Centro Deportivo',
                       'Bolera', 'Centro de Juegos', 'Galería de Arte'],
            'tipos': ['cinema', 'park', 'sports_centre', 'gallery']
        },
        {
            'categoria': 'Finanzas',
            'nombres': ['Banco Nacional', 'Cajero Automático', 'Casa de Cambio',
                       'Agencia de Seguros', 'Oficina de Inversiones'],
            'tipos': ['bank', 'atm', 'money_transfer']
        },
        {
            'categoria': 'Alojamiento',
            'nombres': ['Hotel Plaza', 'Motel Camino', 'Hostal Backpacker',
                       'Suite Ejecutiva', 'Casa de Huéspedes'],
            'tipos': ['hotel', 'motel', 'hostel', 'guest_house']
        }
    ]
    
    servicios = []
    
    for i in range(min(max_results, 80)):
        tipo_servicio = random.choice(catalogo_servicios)
        
        angle = random.uniform(0, 2 * math.pi)
        distance_km = random.uniform(0.1, min(radius_km, 20))
        
        lat_offset = (distance_km / 111) * math.cos(angle)
        lng_offset = (distance_km / 111) * math.sin(angle)
        
        servicio_lat = lat + lat_offset
        servicio_lng = lng + lng_offset
        
        distancia_metros = calcular_distancia(lat, lng, servicio_lat, servicio_lng)
        distancia_km = distancia_metros / 1000
        
        servicios.append({
            'id': f"sim_{i + 1}",
            'nombre': random.choice(tipo_servicio['nombres']),
            'categoria': tipo_servicio['categoria'],
            'tipo_original': random.choice(tipo_servicio['tipos']),
            'distancia_metros': int(distancia_metros),
            'distancia_km': round(distancia_km, 2),
            'distancia_texto': f"{distancia_km:.1f} km",
            'latitud': round(servicio_lat, 6),
            'longitud': round(servicio_lng, 6),
            'direccion': f"Calle {random.randint(1, 100)} #{random.randint(100, 999)}",
            'telefono': f"+52 {random.randint(100, 999)} {random.randint(1000, 9999)}",
            'horario': random.choice(["9:00-18:00", "8:00-20:00", "24 horas", "7:00-22:00"]),
            'website': "",
            'fuente': 'simulacion',
            'nota': 'Servicio simulado - Modo offline'
        })
    
    servicios.sort(key=lambda x: x['distancia_metros'])
    return servicios