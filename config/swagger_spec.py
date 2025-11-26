from flask import Blueprint, jsonify
from datetime import datetime

swagger_bp = Blueprint('swagger', __name__)

@swagger_bp.route('/api/docs')
@swagger_bp.route('/api/docs/')
def swagger_docs():
    """Página completa de documentación Swagger"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sistema de Seguridad - API Documentation</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@3/swagger-ui.css">
        <style>
            body {
                margin: 0;
                padding: 0;
            }
            #swagger-ui {
                padding: 20px;
            }
            .swagger-ui .topbar {
                display: none;
            }
            .info {
                margin: 20px 0;
                padding: 10px;
                background: #f5f5f5;
                border-radius: 5px;
            }
        </style>
    </head>
    <body>
        <div id="swagger-ui"></div>
        
        <script src="https://unpkg.com/swagger-ui-dist@3/swagger-ui-bundle.js"></script>
        <script src="https://unpkg.com/swagger-ui-dist@3/swagger-ui-standalone-preset.js"></script>
        <script>
            window.onload = function() {
                const ui = SwaggerUIBundle({
                    url: '/api/swagger.json',
                    dom_id: '#swagger-ui',
                    deepLinking: true,
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIStandalonePreset
                    ],
                    plugins: [
                        SwaggerUIBundle.plugins.DownloadUrl
                    ],
                    layout: "StandaloneLayout",
                    config: {
                        withCredentials: true,
                        requestInterceptor: (request) => {
                            if (!request.headers) {
                                request.headers = {};
                            }
                            request.headers['Content-Type'] = 'application/json';
                            return request;
                        }
                    }
                });
                
                ui.initOAuth({
                    clientId: 'swagger-ui',
                    realm: 'sistema-seguridad',
                    appName: 'Sistema de Seguridad API'
                });
            };
        </script>
    </body>
    </html>
    '''

@swagger_bp.route('/api/swagger.json')
def swagger_spec():
    """Especificación Swagger en formato JSON - COMPLETA"""
    spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "Sistema de Seguridad API",
            "version": "1.0",
            "description": "API para gestión de usuarios, autenticación, servicios de ubicación e inventario",
            "contact": {
                "email": "soporte@sistemaseguridad.com"
            },
            "license": {
                "name": "MIT",
                "url": "https://opensource.org/licenses/MIT"
            }
        },
        "servers": [
            {
                "url": "http://localhost:5000",
                "description": "Servidor de desarrollo"
            }
        ],
        "tags": [
            {
                "name": "Autenticación",
                "description": "Endpoints para login, registro, 2FA y gestión de sesiones"
            },
            {
                "name": "Ubicación", 
                "description": "Endpoints para gestión de ubicación y servicios cercanos"
            },
            {
                "name": "Usuarios",
                "description": "Endpoints para gestión de usuarios (CRUD)"
            },
            {
                "name": "Sistema",
                "description": "Endpoints de estado y monitoreo del sistema"
            },
            {
                "name": "Inventario",
                "description": "Endpoints para gestión de inventario, productos, movimientos y alertas"
            }
        ],
        "paths": {
            # ===== ENDPOINTS DE AUTENTICACIÓN =====
            "/api/auth/login": {
                "post": {
                    "tags": ["Autenticación"],
                    "summary": "Iniciar sesión",
                    "description": "Autentica un usuario con email y contraseña, inicia flujo 2FA",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "email": {
                                            "type": "string",
                                            "example": "usuario@example.com",
                                            "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
                                        },
                                        "password": {
                                            "type": "string",
                                            "example": "mi_contraseña",
                                            "minLength": 6,
                                            "maxLength": 50
                                        }
                                    },
                                    "required": ["email", "password"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Login exitoso, requiere 2FA",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "message": {"type": "string"},
                                            "user_id": {"type": "integer"},
                                            "user_nombre": {"type": "string"},
                                            "requires_2fa": {"type": "boolean"}
                                        }
                                    }
                                }
                            }
                        },
                        "400": {"description": "Datos inválidos"},
                        "401": {"description": "Credenciales incorrectas"},
                        "403": {"description": "Usuario ya tiene una sesión activa"}
                    }
                }
            },
            "/api/auth/verify-2fa": {
                "post": {
                    "tags": ["Autenticación"],
                    "summary": "Verificar código 2FA",
                    "description": "Verifica el código de autenticación en dos pasos",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "email": {"type": "string", "example": "usuario@example.com"},
                                        "codigo": {"type": "string", "example": "123456"}
                                    },
                                    "required": ["email", "codigo"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Verificación exitosa",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "message": {"type": "string"},
                                            "user": {
                                                "type": "object",
                                                "properties": {
                                                    "id": {"type": "integer"},
                                                    "nombre": {"type": "string"},
                                                    "email": {"type": "string"},
                                                    "rol": {"type": "string"}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "400": {"description": "Código inválido"}
                    }
                }
            },
            "/api/auth/logout": {
                "post": {
                    "tags": ["Autenticación"],
                    "summary": "Cerrar sesión",
                    "description": "Cierra la sesión del usuario actual",
                    "responses": {
                        "200": {
                            "description": "Sesión cerrada exitosamente",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "message": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/auth/register": {
                "post": {
                    "tags": ["Autenticación"],
                    "summary": "Registrar nuevo usuario",
                    "description": "Crea una nueva cuenta de usuario",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "nombre": {"type": "string", "example": "Juan Pérez"},
                                        "email": {"type": "string", "example": "juan@example.com"},
                                        "password": {"type": "string", "example": "contraseña123"},
                                        "confirm_password": {"type": "string", "example": "contraseña123"},
                                        "rol": {"type": "string", "enum": ["admin", "editor", "lector"], "default": "lector"}
                                    },
                                    "required": ["nombre", "email", "password"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Usuario registrado exitosamente",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "message": {"type": "string"},
                                            "user_id": {"type": "integer"}
                                        }
                                    }
                                }
                            }
                        },
                        "400": {"description": "Datos inválidos o email ya existe"}
                    }
                }
            },
            "/api/auth/forgot-password": {
                "post": {
                    "tags": ["Autenticación"],
                    "summary": "Solicitar recuperación de contraseña",
                    "description": "Inicia el proceso de recuperación de contraseña",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "email": {"type": "string", "example": "usuario@example.com"}
                                    },
                                    "required": ["email"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Código de recuperación enviado",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "message": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/auth/verify-reset-code": {
                "post": {
                    "tags": ["Autenticación"],
                    "summary": "Verificar código de restablecimiento",
                    "description": "Verifica el código de restablecimiento de contraseña",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "email": {"type": "string", "example": "usuario@example.com"},
                                        "codigo": {"type": "string", "example": "123456"}
                                    },
                                    "required": ["email", "codigo"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Código verificado correctamente",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "message": {"type": "string"},
                                            "codigo_valido": {"type": "boolean"}
                                        }
                                    }
                                }
                            }
                        },
                        "400": {"description": "Código inválido o expirado"}
                    }
                }
            },
            "/api/auth/reset-password": {
                "post": {
                    "tags": ["Autenticación"],
                    "summary": "Restablecer contraseña",
                    "description": "Restablece la contraseña usando un código de verificación",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "email": {"type": "string", "example": "usuario@example.com"},
                                        "codigo": {"type": "string", "example": "123456"},
                                        "nueva_password": {"type": "string", "example": "nueva_contraseña123"},
                                        "confirm_password": {"type": "string", "example": "nueva_contraseña123"}
                                    },
                                    "required": ["email", "codigo", "nueva_password", "confirm_password"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Contraseña restablecida exitosamente",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "message": {"type": "string"},
                                            "user_email": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        },
                        "400": {"description": "Datos inválidos o códigos no coinciden"}
                    }
                }
            },
            "/api/auth/password-recovery": {
                "post": {
                    "tags": ["Autenticación"],
                    "summary": "Recuperación de contraseña unificada",
                    "description": "Endpoint unificado para todo el proceso de recuperación de contraseña",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "action": {"type": "string", "enum": ["request", "verify", "reset"], "example": "request"},
                                        "email": {"type": "string", "example": "usuario@example.com"},
                                        "codigo": {"type": "string", "example": "123456"},
                                        "nueva_password": {"type": "string", "example": "nueva_contraseña123"},
                                        "confirm_password": {"type": "string", "example": "nueva_contraseña123"}
                                    },
                                    "required": ["action"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Operación completada según la acción",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "message": {"type": "string"},
                                            "action": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            
            # ===== ENDPOINTS DE UBICACIÓN =====
            "/api/location/services": {
                "get": {
                    "tags": ["Ubicación"],
                    "summary": "Obtener servicios cercanos a la ubicación",
                    "description": "Devuelve servicios cercanos usando OpenStreetMap (online) o simulación (offline)",
                    "parameters": [
                        {
                            "name": "lat",
                            "in": "query",
                            "description": "Latitud de la ubicación",
                            "required": False,
                            "schema": {
                                "type": "number",
                                "format": "float",
                                "example": 20.6597
                            }
                        },
                        {
                            "name": "lng", 
                            "in": "query",
                            "description": "Longitud de la ubicación",
                            "required": False,
                            "schema": {
                                "type": "number", 
                                "format": "float",
                                "example": -103.3496
                            }
                        },
                        {
                            "name": "radius",
                            "in": "query",
                            "description": "Radio de búsqueda en metros",
                            "required": False,
                            "schema": {
                                "type": "integer",
                                "default": 3000,
                                "example": 2000
                            }
                        },
                        {
                            "name": "limit",
                            "in": "query",
                            "description": "Límite de resultados",
                            "required": False,
                            "schema": {
                                "type": "integer",
                                "default": 20,
                                "example": 10
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Lista de servicios cercanos",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "servicios": {"type": "array"},
                                            "metadata": {"type": "object"},
                                            "message": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        },
                        "400": {"description": "Parámetros inválidos"},
                        "500": {"description": "Error del servidor"}
                    }
                }
            },
            "/api/location/": {
                "post": {
                    "tags": ["Ubicación"],
                    "summary": "Actualizar ubicación del usuario",
                    "description": "Guarda o actualiza la ubicación actual del usuario",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "latitud": {"type": "number", "example": 20.6597},
                                        "longitud": {"type": "number", "example": -103.3496},
                                        "precision": {"type": "number", "example": 25.5},
                                        "offline": {"type": "boolean", "default": False},
                                        "direccion_cache": {
                                            "type": "object",
                                            "properties": {
                                                "direccion": {"type": "string"},
                                                "ciudad": {"type": "string"},
                                                "pais": {"type": "string"}
                                            }
                                        }
                                    },
                                    "required": ["latitud", "longitud"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Ubicación actualizada",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "message": {"type": "string"},
                                            "ubicacion": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/location/profile/{user_id}": {
                "get": {
                    "tags": ["Ubicación"],
                    "summary": "Obtener ubicación de usuario",
                    "description": "Obtiene la última ubicación registrada de un usuario específico",
                    "parameters": [
                        {
                            "name": "user_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer", "example": 1}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Ubicación del usuario",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "ultima_ubicacion": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        },
                        "404": {"description": "Usuario no encontrado"}
                    }
                }
            },
            "/api/location/current": {
                "get": {
                    "tags": ["Ubicación"],
                    "summary": "Obtener ubicación actual del usuario",
                    "description": "Obtiene la ubicación actual del usuario desde la sesión o base de datos",
                    "responses": {
                        "200": {
                            "description": "Ubicación actual obtenida",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "ubicacion_actual": {"type": "object"},
                                            "fuente": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            
            # ===== ENDPOINTS DE USUARIOS =====
            "/api/users/": {
                "get": {
                    "tags": ["Usuarios"],
                    "summary": "Obtener lista de usuarios",
                    "description": "Obtiene la lista de usuarios con opciones de filtrado",
                    "parameters": [
                        {
                            "name": "nombre",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "string", "example": "Juan"}
                        },
                        {
                            "name": "rol",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "string", "enum": ["admin", "editor", "lector"]}
                        },
                        {
                            "name": "page",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "integer", "default": 1}
                        },
                        {
                            "name": "per_page",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "integer", "default": 10}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Lista de usuarios",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "usuarios": {"type": "array"},
                                            "paginacion": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "post": {
                    "tags": ["Usuarios"],
                    "summary": "Crear nuevo usuario",
                    "description": "Crea un nuevo usuario (requiere permisos de admin)",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "nombre": {"type": "string", "example": "Nuevo Usuario"},
                                        "email": {"type": "string", "example": "nuevo@example.com"},
                                        "password": {"type": "string", "example": "contraseña123"},
                                        "rol": {"type": "string", "enum": ["admin", "editor", "lector"], "default": "lector"}
                                    },
                                    "required": ["nombre", "email", "password"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Usuario creado exitosamente",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "message": {"type": "string"},
                                            "user_id": {"type": "integer"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/users/{user_id}": {
                "get": {
                    "tags": ["Usuarios"],
                    "summary": "Obtener usuario por ID",
                    "description": "Obtiene la información de un usuario específico",
                    "parameters": [
                        {
                            "name": "user_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer", "example": 1}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Información del usuario",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "usuario": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        },
                        "404": {"description": "Usuario no encontrado"}
                    }
                },
                "put": {
                    "tags": ["Usuarios"],
                    "summary": "Actualizar usuario",
                    "description": "Actualiza la información de un usuario (requiere permisos)",
                    "parameters": [
                        {
                            "name": "user_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer", "example": 1}
                        }
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "nombre": {"type": "string"},
                                        "email": {"type": "string"},
                                        "rol": {"type": "string", "enum": ["admin", "editor", "lector"]},
                                        "nueva_password": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Usuario actualizado",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "message": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "delete": {
                    "tags": ["Usuarios"],
                    "summary": "Eliminar usuario",
                    "description": "Elimina un usuario (requiere permisos de admin)",
                    "parameters": [
                        {
                            "name": "user_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer", "example": 1}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Usuario eliminado",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "message": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/user/profile": {
                "get": {
                    "tags": ["Usuarios"],
                    "summary": "Obtener perfil del usuario",
                    "description": "Obtiene la información del perfil del usuario autenticado",
                    "responses": {
                        "200": {
                            "description": "Perfil del usuario",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "user": {"type": "object"},
                                            "ultima_ubicacion": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            
            # ===== ENDPOINTS DEL SISTEMA =====
            "/api/health": {
                "get": {
                    "tags": ["Sistema"],
                    "summary": "Verificar estado del API",
                    "description": "Comprueba que el API esté funcionando correctamente",
                    "responses": {
                        "200": {
                            "description": "API funcionando",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string"},
                                            "message": {"type": "string"},
                                            "timestamp": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/connection/status": {
                "get": {
                    "tags": ["Sistema"],
                    "summary": "Verificar estado de conexión",
                    "description": "Comprueba si el sistema está en modo online u offline",
                    "responses": {
                        "200": {
                            "description": "Estado de conexión",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "online": {"type": "boolean"},
                                            "modo_operacion": {"type": "string"},
                                            "servicios_disponibles": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/sincronizar": {
                "post": {
                    "tags": ["Sistema"],
                    "summary": "Sincronizar datos pendientes",
                    "description": "Sincroniza datos pendientes cuando se restablece la conexión",
                    "responses": {
                        "200": {
                            "description": "Datos sincronizados",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "message": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            
            # ===== ENDPOINTS DE INVENTARIO =====
            "/api/inventario/productos": {
                "get": {
                    "tags": ["Inventario"],
                    "summary": "Obtener lista de productos",
                    "description": "Devuelve todos los productos activos del inventario - Todos los roles",
                    "responses": {
                        "200": {
                            "description": "Lista de productos obtenida exitosamente",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "ID_Producto": {"type": "integer", "example": 1},
                                                "Codigo": {"type": "string", "example": "PROD-001"},
                                                "Nombre": {"type": "string", "example": "Laptop Dell"},
                                                "Descripcion": {"type": "string", "example": "Laptop empresarial"},
                                                "Categoria": {"type": "string", "example": "Tecnología"},
                                                "Unidad": {"type": "string", "example": "Pieza"},
                                                "Stock_Minimo": {"type": "integer", "example": 5},
                                                "Stock_Actual": {"type": "integer", "example": 15},
                                                "Activo": {"type": "boolean", "example": True}
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "401": {"description": "No autorizado"},
                        "500": {"description": "Error del servidor"}
                    }
                },
                "post": {
                    "tags": ["Inventario"],
                    "summary": "Crear nuevo producto",
                    "description": "Agrega un nuevo producto al inventario - Editores y Admins",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "Codigo": {
                                            "type": "string", 
                                            "example": "PROD-001",
                                            "description": "Código único del producto"
                                        },
                                        "Nombre": {
                                            "type": "string", 
                                            "example": "Laptop Dell",
                                            "description": "Nombre del producto"
                                        },
                                        "Descripcion": {
                                            "type": "string", 
                                            "example": "Laptop empresarial i7, 16GB RAM",
                                            "description": "Descripción detallada"
                                        },
                                        "Categoria": {
                                            "type": "string", 
                                            "example": "Tecnología",
                                            "description": "Categoría del producto"
                                        },
                                        "Unidad": {
                                            "type": "string", 
                                            "example": "Pieza",
                                            "description": "Unidad de medida (Pieza, Kilo, Litro, etc.)"
                                        },
                                        "Stock_Minimo": {
                                            "type": "integer", 
                                            "example": 5,
                                            "description": "Stock mínimo recomendado"
                                        },
                                        "Stock_Actual": {
                                            "type": "integer", 
                                            "example": 0,
                                            "description": "Stock actual inicial"
                                        }
                                    },
                                    "required": ["Codigo", "Nombre", "Unidad"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Producto creado exitosamente",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "producto": {"type": "object"},
                                            "message": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        },
                        "400": {"description": "Datos inválidos o código duplicado"},
                        "403": {"description": "No tienes permisos para crear productos"},
                        "401": {"description": "No autorizado"},
                        "500": {"description": "Error del servidor"}
                    }
                }
            },
            
            "/api/inventario/productos/{producto_id}": {
                "put": {
                    "tags": ["Inventario"],
                    "summary": "Actualizar producto",
                    "description": "Actualiza un producto existente con validación de permisos por campo",
                    "parameters": [
                        {
                            "name": "producto_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer", "example": 1}
                        }
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "Codigo": {"type": "string", "example": "PROD-001"},
                                        "Nombre": {"type": "string", "example": "Laptop Dell"},
                                        "Descripcion": {"type": "string", "example": "Laptop empresarial"},
                                        "Categoria": {"type": "string", "example": "Tecnología"},
                                        "Unidad": {"type": "string", "example": "Pieza"},
                                        "Stock_Actual": {"type": "integer", "example": 15}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Producto actualizado",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "message": {"type": "string"},
                                            "campos_actualizados": {"type": "array"}
                                        }
                                    }
                                }
                            }
                        },
                        "403": {"description": "Permisos insuficientes para editar ciertos campos"},
                        "404": {"description": "Producto no encontrado"},
                        "500": {"description": "Error del servidor"}
                    }
                },
                "delete": {
                    "tags": ["Inventario"],
                    "summary": "Eliminar producto",
                    "description": "Elimina un producto (solo administradores)",
                    "parameters": [
                        {
                            "name": "producto_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer", "example": 1}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Producto eliminado",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "message": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        },
                        "403": {"description": "No tienes permisos de administrador"},
                        "404": {"description": "Producto no encontrado"},
                        "500": {"description": "Error del servidor"}
                    }
                }
            },

            "/api/inventario/productos/{producto_id}/desactivar": {
                "put": {
                    "tags": ["Inventario"],
                    "summary": "Desactivar producto",
                    "description": "Desactiva un producto (solo administradores)",
                    "parameters": [
                        {
                            "name": "producto_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer", "example": 1}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Producto desactivado",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "message": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        },
                        "403": {"description": "No tienes permisos de administrador"},
                        "404": {"description": "Producto no encontrado"},
                        "500": {"description": "Error del servidor"}
                    }
                }
            },
            
            "/api/inventario/entradas": {
                "post": {
                    "tags": ["Inventario"],
                    "summary": "Registrar entrada de inventario",
                    "description": "Registra una entrada de productos al inventario (aumenta stock) - Editores y Admins",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "ID_Producto": {
                                            "type": "integer", 
                                            "example": 1,
                                            "description": "ID del producto"
                                        },
                                        "Cantidad": {
                                            "type": "integer", 
                                            "example": 10,
                                            "description": "Cantidad a ingresar"
                                        },
                                        "Referencia_Documento": {
                                            "type": "string", 
                                            "example": "FAC-001",
                                            "description": "Número de factura o documento"
                                        },
                                        "Responsable": {
                                            "type": "string", 
                                            "example": "Juan Pérez",
                                            "description": "Persona que registra la entrada"
                                        },
                                        "ID_Proveedor": {
                                            "type": "integer", 
                                            "example": 1,
                                            "description": "ID del proveedor (opcional)"
                                        }
                                    },
                                    "required": ["ID_Producto", "Cantidad", "Responsable"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Entrada registrada exitosamente",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "movimiento": {"type": "object"},
                                            "nuevo_stock": {"type": "integer"},
                                            "message": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        },
                        "400": {"description": "Datos inválidos o producto no encontrado"},
                        "403": {"description": "No tienes permisos para registrar entradas"},
                        "401": {"description": "No autorizado"},
                        "500": {"description": "Error del servidor"}
                    }
                }
            },
            
            "/api/inventario/salidas": {
                "post": {
                    "tags": ["Inventario"],
                    "summary": "Registrar salida de inventario",
                    "description": "Registra una salida de productos del inventario (reduce stock) - Editores y Admins",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "ID_Producto": {
                                            "type": "integer", 
                                            "example": 1,
                                            "description": "ID del producto"
                                        },
                                        "Cantidad": {
                                            "type": "integer", 
                                            "example": 2,
                                            "description": "Cantidad a retirar"
                                        },
                                        "Referencia_Documento": {
                                            "type": "string", 
                                            "example": "VENTA-001",
                                            "description": "Número de venta o documento"
                                        },
                                        "Responsable": {
                                            "type": "string", 
                                            "example": "María García",
                                            "description": "Persona que registra la salida"
                                        },
                                        "ID_Cliente": {
                                            "type": "integer", 
                                            "example": 1,
                                            "description": "ID del cliente (opcional)"
                                        }
                                    },
                                    "required": ["ID_Producto", "Cantidad", "Responsable"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Salida registrada exitosamente",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "movimiento": {"type": "object"},
                                            "nuevo_stock": {"type": "integer"},
                                            "message": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        },
                        "400": {"description": "Datos inválidos, producto no encontrado o stock insuficiente"},
                        "403": {"description": "No tienes permisos para registrar salidas"},
                        "401": {"description": "No autorizado"},
                        "500": {"description": "Error del servidor"}
                    }
                }
            },
            
            "/api/inventario/alertas": {
                "get": {
                    "tags": ["Inventario"],
                    "summary": "Obtener alertas de stock bajo",
                    "description": "Devuelve productos con stock por debajo del mínimo establecido - Todos los roles",
                    "responses": {
                        "200": {
                            "description": "Lista de alertas de stock bajo",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "ID_Producto": {"type": "integer", "example": 1},
                                                "Codigo": {"type": "string", "example": "PROD-001"},
                                                "Nombre": {"type": "string", "example": "Laptop Dell"},
                                                "Stock_Minimo": {"type": "integer", "example": 5},
                                                "Stock_Actual": {"type": "integer", "example": 2},
                                                "Diferencia": {"type": "integer", "example": 3},
                                                "Alerta": {"type": "string", "example": "Stock crítico"}
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "401": {"description": "No autorizado"},
                        "500": {"description": "Error del servidor"}
                    }
                }
            },
            
            "/api/inventario/movimientos": {
                "get": {
                    "tags": ["Inventario"],
                    "summary": "Obtener historial de movimientos",
                    "description": "Devuelve el historial completo de entradas y salidas del inventario - Todos los roles",
                    "parameters": [
                        {
                            "name": "producto_id",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "integer", "example": 1},
                            "description": "Filtrar por ID de producto"
                        },
                        {
                            "name": "tipo",
                            "in": "query", 
                            "required": False,
                            "schema": {"type": "string", "enum": ["Entrada", "Salida"]},
                            "description": "Filtrar por tipo de movimiento"
                        },
                        {
                            "name": "limit",
                            "in": "query",
                            "required": False, 
                            "schema": {"type": "integer", "default": 50},
                            "description": "Límite de resultados"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Historial de movimientos",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "ID_Movimiento": {"type": "integer", "example": 1},
                                                "Fecha": {"type": "string", "example": "2024-01-15T10:30:00"},
                                                "Tipo": {"type": "string", "example": "Entrada"},
                                                "Producto_Nombre": {"type": "string", "example": "Laptop Dell"},
                                                "Cantidad": {"type": "integer", "example": 10},
                                                "Referencia_Documento": {"type": "string", "example": "FAC-001"},
                                                "Responsable": {"type": "string", "example": "Juan Pérez"}
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "401": {"description": "No autorizado"},
                        "500": {"description": "Error del servidor"}
                    }
                }
            },
            
            "/api/inventario/proveedores": {
                "get": {
                    "tags": ["Inventario"],
                    "summary": "Obtener lista de proveedores",
                    "description": "Devuelve todos los proveedores activos - Todos los roles",
                    "responses": {
                        "200": {
                            "description": "Lista de proveedores",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "ID_Proveedor": {"type": "integer", "example": 1},
                                                "Nombre": {"type": "string", "example": "Tecnología S.A."},
                                                "Telefono": {"type": "string", "example": "+1234567890"},
                                                "Contacto": {"type": "string", "example": "Carlos López"},
                                                "Email": {"type": "string", "example": "carlos@tecnologia.com"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "post": {
                    "tags": ["Inventario"],
                    "summary": "Crear nuevo proveedor",
                    "description": "Agrega un nuevo proveedor al sistema - Editores y Admins",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "Nombre": {"type": "string", "example": "Tecnología S.A."},
                                        "Telefono": {"type": "string", "example": "+1234567890"},
                                        "Contacto": {"type": "string", "example": "Carlos López"},
                                        "Email": {"type": "string", "example": "carlos@tecnologia.com"}
                                    },
                                    "required": ["Nombre"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Proveedor creado exitosamente",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "proveedor": {"type": "object"},
                                            "message": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        },
                        "403": {"description": "No tienes permisos para crear proveedores"},
                        "400": {"description": "Datos inválidos"},
                        "500": {"description": "Error del servidor"}
                    }
                }
            },
            
            "/api/inventario/clientes": {
                "get": {
                    "tags": ["Inventario"],
                    "summary": "Obtener lista de clientes", 
                    "description": "Devuelve todos los clientes activos - Todos los roles",
                    "responses": {
                        "200": {
                            "description": "Lista de clientes",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array", 
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "ID_Cliente": {"type": "integer", "example": 1},
                                                "Nombre": {"type": "string", "example": "Empresa ABC"},
                                                "Telefono": {"type": "string", "example": "+0987654321"},
                                                "Contacto": {"type": "string", "example": "Ana Martínez"},
                                                "Email": {"type": "string", "example": "ana@empresaabc.com"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "post": {
                    "tags": ["Inventario"],
                    "summary": "Crear nuevo cliente",
                    "description": "Agrega un nuevo cliente al sistema - Editores y Admins", 
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "Nombre": {"type": "string", "example": "Empresa ABC"},
                                        "Telefono": {"type": "string", "example": "+0987654321"}, 
                                        "Contacto": {"type": "string", "example": "Ana Martínez"},
                                        "Email": {"type": "string", "example": "ana@empresaabc.com"}
                                    },
                                    "required": ["Nombre"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Cliente creado exitosamente",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "cliente": {"type": "object"},
                                            "message": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        },
                        "403": {"description": "No tienes permisos para crear clientes"},
                        "400": {"description": "Datos inválidos"},
                        "500": {"description": "Error del servidor"}
                    }
                }
            },

            # ===== NUEVOS ENDPOINTS DE REPORTES =====
            "/api/inventario/reportes/stock-bajo": {
                "get": {
                    "tags": ["Inventario"],
                    "summary": "Reporte de stock bajo",
                    "description": "Devuelve productos con stock por debajo del mínimo - Todos los roles",
                    "responses": {
                        "200": {
                            "description": "Reporte de stock bajo generado",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "ID_Producto": {"type": "integer"},
                                                "Codigo": {"type": "string"},
                                                "Nombre": {"type": "string"},
                                                "Stock_Minimo": {"type": "integer"},
                                                "Stock_Actual": {"type": "integer"},
                                                "Diferencia": {"type": "integer"},
                                                "Alerta": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },

            "/api/inventario/reportes/movimientos-detallados": {
                "get": {
                    "tags": ["Inventario"],
                    "summary": "Reporte detallado de movimientos",
                    "description": "Devuelve reporte detallado de movimientos con filtros - Todos los roles",
                    "parameters": [
                        {
                            "name": "fecha_inicio",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "string", "format": "date"},
                            "description": "Fecha de inicio del reporte"
                        },
                        {
                            "name": "fecha_fin",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "string", "format": "date"},
                            "description": "Fecha de fin del reporte"
                        },
                        {
                            "name": "producto_id",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "integer"},
                            "description": "Filtrar por ID de producto"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Reporte detallado generado",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "movimientos": {"type": "array"},
                                            "resumen": {
                                                "type": "object",
                                                "properties": {
                                                    "total_entradas": {"type": "integer"},
                                                    "total_salidas": {"type": "integer"},
                                                    "total_movimientos": {"type": "integer"}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "Error": {
                    "type": "object",
                    "properties": {
                        "error": {"type": "string"},
                        "message": {"type": "string"},
                        "code": {"type": "integer"}
                    }
                },
                "Success": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "message": {"type": "string"}
                    }
                }
            },
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT"
                },
                "SessionAuth": {
                    "type": "apiKey",
                    "in": "cookie",
                    "name": "session"
                }
            }
        },
        "security": [
            {
                "BearerAuth": []
            },
            {
                "SessionAuth": []
            }
        ]
    }
    return jsonify(spec)

@swagger_bp.route('/api/health')
def health_check():
    """Endpoint de salud para Swagger"""
    return jsonify({
        'status': 'healthy',
        'message': 'Sistema de Seguridad API está funcionando correctamente',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0'
    })