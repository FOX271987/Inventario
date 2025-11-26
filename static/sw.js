const CACHE_NAME = 'seguridad-app-v9';
const MAP_CACHE_NAME = 'map-data-v3';
const urlsToCache = [
  '/',
  '/login',
  '/registro',
  '/olvide-contrasena',
  '/verificar-2fa',
  '/verificar-recuperacion',
  '/verificar-social',
  '/offline',
  '/ubicacion',
  
  // Bootstrap CSS local
  '/static/css/bootstrap.min.css',
  
  // Bootstrap Icons local
  '/static/css/bootstrap-icons.css',
  
  // Fuentes de Bootstrap Icons
  '/static/css/fonts/bootstrap-icons.woff',
  '/static/css/fonts/bootstrap-icons.woff2',
  
  // Bootstrap JS local
  '/static/js/bootstrap.bundle.min.js',
  
  // jQuery local
  '/static/js/jquery.min.js',
  
  // Estilos personalizados
  '/static/css/styles.css',
  
  // JavaScript personalizado
  '/static/js/app.js',
  
  // Logo y favicon
  '/static/images/logo.png',
  '/favicon.ico',

  // Leaflet local (si está disponible)
  '/static/css/leaflet.css',
  '/static/js/leaflet.js'
];

// Almacenar ubicaciones pendientes cuando hay conexión
async function almacenarUbicacionOffline(ubicacionData) {
    try {
        const cache = await caches.open('ubicaciones-pendientes');
        const id = Date.now().toString();
        const response = new Response(JSON.stringify(ubicacionData), {
            headers: { 'Content-Type': 'application/json' }
        });
        await cache.put(`/ubicacion-pendiente-${id}`, response);
        console.log('Ubicación guardada para sincronización posterior:', id);
        return true;
    } catch (error) {
        console.error('Error guardando ubicación offline:', error);
        return false;
    }
}

// Cachear datos de mapas y servicios
async function cachearDatosMapa(url, data) {
    try {
        const cache = await caches.open(MAP_CACHE_NAME);
        const response = new Response(JSON.stringify(data), {
            headers: { 'Content-Type': 'application/json' }
        });
        await cache.put(url, response);
        console.log('Datos de mapa cacheados:', url);
        return true;
    } catch (error) {
        console.error('Error cacheando datos de mapa:', error);
        return false;
    }
}

// Obtener datos de mapa del cache
async function obtenerDatosMapaCache(url) {
    try {
        const cache = await caches.open(MAP_CACHE_NAME);
        const response = await cache.match(url);
        if (response) {
            const data = await response.json();
            console.log('Datos obtenidos del cache:', url);
            return data;
        }
        return null;
    } catch (error) {
        console.error('Error obteniendo datos del cache:', error);
        return null;
    }
}

// Generar servicios simulados para modo offline
function generarServiciosOffline(lat, lon, radio = 3000) {
    console.log('Generando servicios simulados para modo offline');
    
    const tiposServicios = [
        { amenity: 'restaurant', name: 'Restaurante Local', symbol: '🍽️' },
        { amenity: 'cafe', name: 'Cafetería Central', symbol: '☕' },
        { amenity: 'pharmacy', name: 'Farmacia del Pueblo', symbol: '💊' },
        { amenity: 'bank', name: 'Banco Nacional', symbol: '🏦' },
        { amenity: 'supermarket', name: 'Supermercado Municipal', symbol: '🛒' },
        { amenity: 'hospital', name: 'Centro de Salud', symbol: '🏥' },
        { amenity: 'fuel', name: 'Estación de Servicio', symbol: '⛽' },
        { amenity: 'school', name: 'Escuela Primaria', symbol: '🏫' },
        { amenity: 'library', name: 'Biblioteca Pública', symbol: '📚' },
        { amenity: 'police', name: 'Estación de Policía', symbol: '👮' }
    ];

    const servicios = [];
    
    // Generar 8-15 servicios simulados alrededor de la ubicación
    const cantidad = 8 + Math.floor(Math.random() * 8);
    
    for (let i = 0; i < cantidad; i++) {
        const tipo = tiposServicios[i % tiposServicios.length];
        const angulo = (i / cantidad) * 2 * Math.PI;
        const distancia = (radio / 1000) * (0.2 + Math.random() * 0.8);
        
        // Calcular nueva posición (aproximación simple)
        const deltaLat = (distancia / 110.574) * Math.cos(angulo);
        const deltaLon = (distancia / (111.320 * Math.cos(lat * Math.PI / 180))) * Math.sin(angulo);
        
        servicios.push({
            type: 'node',
            id: -1000 - i,
            lat: lat + deltaLat,
            lon: lon + deltaLon,
            tags: {
                amenity: tipo.amenity,
                name: `${tipo.name} ${i + 1}`,
                'simulated': 'true'
            },
            distancia: distancia * 1000
        });
    }
    
    return {
        elements: servicios,
        offline: true,
        timestamp: new Date().toISOString(),
        generated: cantidad
    };
}

// Sincronizar ubicaciones pendientes cuando se recupera la conexión
async function sincronizarUbicacionesPendientes() {
    try {
        const cache = await caches.open('ubicaciones-pendientes');
        const keys = await cache.keys();
        
        console.log(`Sincronizando ${keys.length} ubicaciones pendientes...`);
        
        for (const request of keys) {
            try {
                const response = await cache.match(request);
                const ubicacionData = await response.json();
                
                console.log('Sincronizando ubicación:', ubicacionData);
                
                // Intentar enviar al servidor
                const syncResponse = await fetch('/api/actualizar-ubicacion', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(ubicacionData)
                });
                
                if (syncResponse.ok) {
                    await cache.delete(request);
                    console.log('Ubicación sincronizada exitosamente:', request.url);
                } else {
                    console.log('Error en respuesta del servidor:', syncResponse.status);
                }
            } catch (error) {
                console.error('Error sincronizando ubicación específica:', error);
            }
        }
        
        // Notificar a las pestañas abiertas
        const clients = await self.clients.matchAll();
        clients.forEach(client => {
            client.postMessage({
                type: 'SYNC_COMPLETE',
                message: `Sincronización completada. ${keys.length} ubicaciones procesadas.`
            });
        });
        
    } catch (error) {
        console.error('Error en sincronización de ubicaciones:', error);
    }
}

// Obtener todas las ubicaciones pendientes
async function obtenerUbicacionesPendientes() {
    try {
        const cache = await caches.open('ubicaciones-pendientes');
        const keys = await cache.keys();
        const ubicaciones = [];
        
        for (const request of keys) {
            const response = await cache.match(request);
            const data = await response.json();
            ubicaciones.push(data);
        }
        
        return ubicaciones;
    } catch (error) {
        console.error('Error obteniendo ubicaciones pendientes:', error);
        return [];
    }
}

self.addEventListener('install', (event) => {
    console.log('Service Worker instalando...');
    event.waitUntil(
        (async () => {
            // Abrir cache de recursos estáticos
            const cache = await caches.open(CACHE_NAME);
            console.log('Cache abierto, agregando recursos...');
            
            try {
                // Cachear recursos locales (excluyendo Leaflet por ahora)
                const localUrls = urlsToCache.filter(url => 
                    !url.includes('leaflet') && !url.includes('://')
                );
                
                await cache.addAll(localUrls.map(url => new Request(url, { cache: 'reload' })));
                console.log('Recursos locales cacheados');
                
            } catch (error) {
                console.log('Error cacheando algunos recursos:', error);
            }
            
            // Registrar background sync para ubicaciones
            if ('sync' in self.registration) {
                try {
                    await self.registration.sync.register('sync-ubicaciones');
                    console.log('Background sync registrado para ubicaciones');
                } catch (error) {
                    console.log('Background sync no disponible:', error);
                }
            }
            
            return self.skipWaiting();
        })()
    );
});

self.addEventListener('activate', (event) => {
    console.log('Service Worker activado');
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME && 
                        cacheName !== 'ubicaciones-pendientes' && 
                        cacheName !== MAP_CACHE_NAME) {
                        console.log('Eliminando cache antiguo:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            console.log('Service Worker listo para controlar clientes');
            return self.clients.claim();
        })
    );
});

self.addEventListener('fetch', (event) => {
    const url = event.request.url;
    
    // Manejar solicitudes POST de ubicación
    if (event.request.method === 'POST' && url.includes('/api/actualizar-ubicacion')) {
        event.respondWith(
            (async () => {
                try {
                    const networkResponse = await fetch(event.request.clone());
                    
                    if (networkResponse.ok) {
                        console.log('Ubicación enviada online exitosamente');
                        return networkResponse;
                    } else {
                        throw new Error('Network response not OK');
                    }
                } catch (error) {
                    // Fallback offline
                    console.log('Modo offline - guardando ubicación localmente');
                    
                    try {
                        const requestClone = event.request.clone();
                        const data = await requestClone.json();
                        
                        const ubicacionOffline = {
                            ...data,
                            timestamp: new Date().toISOString(),
                            intentoSincronizacion: true,
                            offline: true
                        };
                        
                        const exito = await almacenarUbicacionOffline(ubicacionOffline);
                        
                        if (exito) {
                            const clients = await self.clients.matchAll();
                            clients.forEach(client => {
                                client.postMessage({
                                    type: 'UBICACION_GUARDADA_OFFLINE',
                                    data: ubicacionOffline,
                                    message: 'Ubicación guardada para sincronización posterior'
                                });
                            });
                            
                            return new Response(JSON.stringify({ 
                                success: true, 
                                message: 'Ubicación guardada para sincronización posterior',
                                offline: true,
                                timestamp: ubicacionOffline.timestamp
                            }), {
                                status: 200,
                                headers: { 'Content-Type': 'application/json' }
                            });
                        } else {
                            throw new Error('Error guardando ubicación offline');
                        }
                    } catch (parseError) {
                        console.error('Error procesando ubicación offline:', parseError);
                        return new Response(JSON.stringify({ 
                            success: false, 
                            message: 'Error procesando ubicación offline' 
                        }), {
                            status: 500,
                            headers: { 'Content-Type': 'application/json' }
                        });
                    }
                }
            })()
        );
        return;
    }

    // Manejar solicitudes a Overpass API
    if (url.includes('overpass-api.de/api/interpreter')) {
        event.respondWith(
            (async () => {
                try {
                    const networkResponse = await fetch(event.request);
                    
                    if (networkResponse.ok) {
                        const data = await networkResponse.json();
                        await cachearDatosMapa(url, data);
                        return networkResponse;
                    } else {
                        throw new Error('Network response not OK');
                    }
                } catch (error) {
                    console.log('Modo offline para servicios de mapa');
                    
                    const cachedData = await obtenerDatosMapaCache(url);
                    if (cachedData) {
                        return new Response(JSON.stringify(cachedData), {
                            status: 200,
                            headers: { 'Content-Type': 'application/json' }
                        });
                    }
                    
                    // Generar servicios simulados
                    try {
                        const requestBody = await event.request.text();
                        const coordMatch = requestBody.match(/around:\d+,([-\d.]+),([-\d.]+)/);
                        if (coordMatch) {
                            const lat = parseFloat(coordMatch[1]);
                            const lon = parseFloat(coordMatch[2]);
                            const radioMatch = requestBody.match(/around:(\d+)/);
                            const radio = radioMatch ? parseInt(radioMatch[1]) : 3000;
                            
                            const serviciosSimulados = generarServiciosOffline(lat, lon, radio);
                            
                            return new Response(JSON.stringify(serviciosSimulados), {
                                status: 200,
                                headers: { 'Content-Type': 'application/json' }
                            });
                        }
                    } catch (parseError) {
                        console.error('Error generando servicios simulados:', parseError);
                    }
                    
                    return new Response(JSON.stringify({ 
                        elements: [],
                        offline: true,
                        error: 'Modo offline - sin datos disponibles'
                    }), {
                        status: 200,
                        headers: { 'Content-Type': 'application/json' }
                    });
                }
            })()
        );
        return;
    }

    // Manejar solicitudes a Nominatim
    if (url.includes('nominatim.openstreetmap.org/reverse')) {
        event.respondWith(
            (async () => {
                try {
                    const networkResponse = await fetch(event.request);
                    
                    if (networkResponse.ok) {
                        const data = await networkResponse.json();
                        await cachearDatosMapa(url, data);
                        return networkResponse;
                    } else {
                        throw new Error('Network response not OK');
                    }
                } catch (error) {
                    console.log('Modo offline para geocodificación');
                    
                    const cachedData = await obtenerDatosMapaCache(url);
                    if (cachedData) {
                        return new Response(JSON.stringify(cachedData), {
                            status: 200,
                            headers: { 'Content-Type': 'application/json' }
                        });
                    }
                    
                    const urlObj = new URL(url);
                    const lat = urlObj.searchParams.get('lat');
                    const lon = urlObj.searchParams.get('lon');
                    
                    const direccionSimulada = {
                        display_name: `Ubicación aproximada (Modo Offline)\nLat: ${lat}, Lon: ${lon}`,
                        address: {
                            road: 'Calle Desconocida',
                            city: 'Ciudad',
                            country: 'País'
                        },
                        offline: true,
                        simulated: true
                    };
                    
                    return new Response(JSON.stringify(direccionSimulada), {
                        status: 200,
                        headers: { 'Content-Type': 'application/json' }
                    });
                }
            })()
        );
        return;
    }

    // Solo manejar solicitudes GET a partir de aquí
    if (event.request.method !== 'GET') return;

    // Para recursos Leaflet - red primero, sin cache agresivo
    if (url.includes('leaflet')) {
        event.respondWith(
            (async () => {
                try {
                    // Siempre intentar la red primero para Leaflet
                    const networkResponse = await fetch(event.request);
                    return networkResponse;
                } catch (error) {
                    // Solo usar cache si la red falla completamente
                    const cachedResponse = await caches.match(event.request);
                    if (cachedResponse) {
                        return cachedResponse;
                    }
                    return new Response('', { status: 404 });
                }
            })()
        );
        return;
    }

    // Para páginas HTML
    if (event.request.mode === 'navigate') {
        event.respondWith(
            (async () => {
                try {
                    const networkResponse = await fetch(event.request);
                    return networkResponse;
                } catch (error) {
                    const offlineResponse = await caches.match('/offline');
                    return offlineResponse || new Response('Modo offline', {
                        status: 503,
                        headers: { 'Content-Type': 'text/html' }
                    });
                }
            })()
        );
        return;
    }

    // Para recursos estáticos
    if (url.includes('/static/') || url.includes('/offline')) {
        event.respondWith(
            caches.match(event.request)
                .then((response) => {
                    if (response) {
                        return response;
                    }
                    return fetch(event.request)
                        .then(networkResponse => {
                            if (networkResponse.ok) {
                                caches.open(CACHE_NAME)
                                    .then(cache => cache.put(event.request, networkResponse.clone()));
                            }
                            return networkResponse;
                        })
                        .catch(error => {
                            return new Response('', { 
                                status: 404, 
                                statusText: 'Not Found' 
                            });
                        });
                })
        );
        return;
    }

    // Para APIs de datos
    if (url.includes('/api/')) {
        event.respondWith(
            fetch(event.request)
                .then(networkResponse => {
                    return networkResponse;
                })
                .catch(error => {
                    if (url.includes('/api/servicios-cercanos')) {
                        return new Response(JSON.stringify({
                            servicios: [
                                {
                                    nombre: 'Modo Offline - Servicios no disponibles',
                                    tipo: 'offline',
                                    distancia: 'N/A',
                                    direccion: 'Conecta a internet para ver servicios en tiempo real',
                                    telefono: 'N/A',
                                    offline: true
                                }
                            ],
                            offline: true
                        }), {
                            status: 200,
                            headers: { 'Content-Type': 'application/json' }
                        });
                    }
                    
                    if (url.includes('/api/preferencias')) {
                        return new Response(JSON.stringify({
                            tema: 'light',
                            notificaciones: false,
                            tamaño_texto: 'medium',
                            offline: true
                        }), {
                            status: 200,
                            headers: { 'Content-Type': 'application/json' }
                        });
                    }
                    
                    return new Response(JSON.stringify({ 
                        error: 'Offline mode',
                        message: 'Conecta a internet para acceder a esta funcionalidad',
                        offline: true
                    }), {
                        status: 503,
                        headers: { 'Content-Type': 'application/json' }
                    });
                })
        );
        return;
    }

    // Estrategia por defecto
    event.respondWith(
        fetch(event.request)
            .then(networkResponse => {
                return networkResponse;
            })
            .catch(error => {
                return caches.match(event.request)
                    .then(cacheResponse => {
                        return cacheResponse || new Response('Resource not available offline', {
                            status: 404,
                            statusText: 'Not Found'
                        });
                    });
            })
    );
});

// Background sync
self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-ubicaciones') {
        console.log('Background Sync activado: Sincronizando ubicaciones pendientes...');
        event.waitUntil(sincronizarUbicacionesPendientes());
    }
});

// Manejar mensajes
self.addEventListener('message', (event) => {
    const { type, data } = event.data;
    
    switch (type) {
        case 'GET_PENDING_LOCATIONS':
            event.waitUntil(
                obtenerUbicacionesPendientes().then(ubicaciones => {
                    event.ports[0].postMessage({
                        type: 'PENDING_LOCATIONS_RESPONSE',
                        data: ubicaciones
                    });
                })
            );
            break;
            
        case 'CLEAR_PENDING_LOCATIONS':
            event.waitUntil(
                caches.open('ubicaciones-pendientes').then(cache => {
                    return cache.keys().then(keys => {
                        return Promise.all(keys.map(key => cache.delete(key)));
                    });
                }).then(() => {
                    event.ports[0].postMessage({
                        type: 'CLEAR_COMPLETE',
                        message: 'Ubicaciones pendientes eliminadas'
                    });
                })
            );
            break;
            
        case 'MANUAL_SYNC':
            event.waitUntil(
                sincronizarUbicacionesPendientes().then(() => {
                    event.ports[0].postMessage({
                        type: 'MANUAL_SYNC_COMPLETE',
                        message: 'Sincronización manual completada'
                    });
                })
            );
            break;

        case 'CACHE_MAP_DATA':
            event.waitUntil(
                cachearDatosMapa(data.url, data.content).then(success => {
                    event.ports[0].postMessage({
                        type: 'CACHE_MAP_DATA_RESPONSE',
                        success: success
                    });
                })
            );
            break;

        case 'GET_CACHED_MAP_DATA':
            event.waitUntil(
                obtenerDatosMapaCache(data.url).then(cachedData => {
                    event.ports[0].postMessage({
                        type: 'CACHED_MAP_DATA_RESPONSE',
                        data: cachedData
                    });
                })
            );
            break;
            
        default:
            console.log('Mensaje no reconocido:', type);
    }
});

// Notificaciones push
self.addEventListener('push', (event) => {
    if (!event.data) return;
    
    try {
        const data = event.data.json();
        const options = {
            body: data.body || 'Nueva actualización disponible',
            icon: '/static/images/logo.png',
            badge: '/static/images/logo.png',
            tag: data.tag || 'general-notification',
            requireInteraction: true,
            actions: [
                {
                    action: 'open',
                    title: 'Abrir aplicación'
                },
                {
                    action: 'close',
                    title: 'Cerrar'
                }
            ]
        };
        
        event.waitUntil(
            self.registration.showNotification(data.title || 'Sistema de Seguridad', options)
        );
    } catch (error) {
        console.log('Error mostrando notificación push:', error);
    }
});

// Clics en notificaciones
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    
    if (event.action === 'open') {
        event.waitUntil(
            self.clients.matchAll({ type: 'window' }).then(clientList => {
                for (const client of clientList) {
                    if (client.url.includes('/') && 'focus' in client) {
                        return client.focus();
                    }
                }
                if (self.clients.openWindow) {
                    return self.clients.openWindow('/');
                }
            })
        );
    }
});

console.log('Service Worker cargado y listo para geolocalización offline');