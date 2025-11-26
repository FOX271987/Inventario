// Variables globales
let productos = [];
let categorias = [];
let proveedores = [];
let clientes = [];

// Función para obtener el rol del usuario desde data attribute
function obtenerRolUsuario() {
    return document.body.getAttribute('data-user-rol') || 'lector';
}

// Función para verificar permisos
function tienePermiso(accion) {
    const rol = obtenerRolUsuario();
    
    if (rol === 'admin') return true;
    if (rol === 'editor' && (accion === 'crear' || accion === 'editar' || accion === 'movimientos')) return true;
    if (rol === 'lector') return false;
    
    return false;
}

// Función para filtrar productos en el frontend
function filtrarProductosEnFrontend(productos) {
    const buscar = document.getElementById('buscarProducto').value.toLowerCase();
    const categoria = document.getElementById('filtroCategoria').value;
    const estado = document.getElementById('filtroEstado').value;
    const stock = document.getElementById('filtroStock').value;

    console.log('🔍 Aplicando filtros frontend:', { 
        buscar, 
        categoria, 
        estado: estado || '(TODOS)', // Muestra "TODOS" si está vacío
        stock 
    });

    return productos.filter(producto => {
        // Filtro por búsqueda (código, nombre o descripción)
        if (buscar) {
            const matchCodigo = producto.Codigo.toLowerCase().includes(buscar);
            const matchNombre = producto.Nombre.toLowerCase().includes(buscar);
            const matchDescripcion = producto.Descripcion ? 
                producto.Descripcion.toLowerCase().includes(buscar) : false;
            
            if (!matchCodigo && !matchNombre && !matchDescripcion) {
                return false;
            }
        }

        // Filtro por categoría
        if (categoria && producto.Categoria !== categoria) {
            return false;
        }

        // ✅ FILTRO POR ESTADO CORREGIDO
        if (estado === 'activo' && !producto.Activo) {
            return false;
        }
        if (estado === 'inactivo' && producto.Activo) {
            return false;
        }
        // Si estado está vacío (""), mostrar TODOS los productos

        // ✅ FILTRO POR STOCK CORREGIDO - Solo aplicar a productos activos
        if (stock) {
            // Solo aplicar filtro de stock a productos activos
            if (producto.Activo) {
                if (stock === 'bajo' && (producto.Stock_Actual >= producto.Stock_Minimo || producto.Stock_Actual === 0)) {
                    return false;
                }
                if (stock === 'normal' && producto.Stock_Actual < producto.Stock_Minimo) {
                    return false;
                }
                if (stock === 'sin' && producto.Stock_Actual > 0) {
                    return false;
                }
            }
            // Si el producto está inactivo, mostrar sin importar el stock
        }

        return true;
    });
}

// Función principal CORREGIDA
function cargarProductos() {
    const buscar = document.getElementById('buscarProducto').value;
    const categoria = document.getElementById('filtroCategoria').value;
    const estado = document.getElementById('filtroEstado').value;
    const stock = document.getElementById('filtroStock').value;

    console.log('Filtros aplicados:', { buscar, categoria, estado, stock });
    
    mostrarCargandoTabla();

    // Construir URL con el filtro de estado CORREGIDO
    const params = new URLSearchParams();
    if (buscar) params.append('buscar', buscar);
    if (categoria) params.append('categoria', categoria);
    if (estado) params.append('estado', estado); // Ahora sí envía el filtro
    if (stock) params.append('stock', stock);
    
    const url = `/api/inventario/productos?${params.toString()}`;
    
    console.log('📡 URL backend:', url);

    fetch(url)
        .then(response => {
            if (!response.ok) throw new Error('Error al cargar productos');
            return response.json();
        })
        .then(data => {
            console.log('✅ Productos del backend:', data.length);
            
            productos = data;
            renderizarTablaProductos(data);
            actualizarEstadisticas(data);
            cargarCategorias();
        })
        .catch(error => {
            console.error('Error:', error);
            mostrarError('Error al cargar los productos: ' + error.message);
        });
}

function renderizarTablaProductos(productos) {
    const tbody = document.getElementById('cuerpoTabla');
    const sinResultados = document.getElementById('sinResultados');
    
    if (productos.length === 0) {
        tbody.innerHTML = '';
        sinResultados.style.display = 'block';
        return;
    }
    
    sinResultados.style.display = 'none';
    
    tbody.innerHTML = productos.map(producto => `
        <tr class="${!producto.Activo ? 'producto-inactivo' : ''} ${getClaseStock(producto)}">
            <td>
                <strong>${escapeHtml(producto.Codigo)}</strong>
                ${!producto.Activo ? '<br><small class="text-muted">Inactivo</small>' : ''}
            </td>
            <td>
                <div class="fw-bold">${escapeHtml(producto.Nombre)}</div>
                ${producto.Descripcion ? `<small class="text-muted">${escapeHtml(producto.Descripcion.substring(0, 50))}${producto.Descripcion.length > 50 ? '...' : ''}</small>` : ''}
            </td>
            <td>${producto.Categoria ? escapeHtml(producto.Categoria) : '<span class="text-muted">N/A</span>'}</td>
            <td>${escapeHtml(producto.Unidad)}</td>
            <td>
                <span class="badge bg-secondary">${producto.Stock_Minimo}</span>
            </td>
            <td>
                <span class="badge ${getBadgeStock(producto)} badge-stock">
                    ${producto.Stock_Actual}
                </span>
                ${producto.Stock_Actual < producto.Stock_Minimo && producto.Stock_Actual > 0 ? 
                  `<br><small class="text-warning">↓ ${producto.Stock_Minimo - producto.Stock_Actual}</small>` : ''}
                ${producto.Stock_Actual === 0 ? '<br><small class="text-danger">Agotado</small>' : ''}
            </td>
            <td>
                <span class="badge ${producto.Activo ? 'bg-success' : 'bg-secondary'}">
                    ${producto.Activo ? 'Activo' : 'Inactivo'}
                </span>
            </td>
            <td>
                <div class="acciones-rapidas">
                    <button class="btn btn-sm btn-outline-primary" onclick="editarProducto(${producto.ID_Producto})" 
                            title="Editar" ${!producto.Activo ? 'disabled' : ''}>
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-success" onclick="nuevoMovimiento('entrada', ${producto.ID_Producto})" 
                            title="Entrada">
                        <i class="bi bi-arrow-down"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-warning" onclick="nuevoMovimiento('salida', ${producto.ID_Producto})" 
                            title="Salida" ${producto.Stock_Actual === 0 ? 'disabled' : ''}>
                        <i class="bi bi-arrow-up"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-info" onclick="verHistorial(${producto.ID_Producto})" 
                            title="Historial">
                        <i class="bi bi-clock-history"></i>
                    </button>
                    ${getBotonesAdmin(producto)}
                </div>
            </td>
        </tr>
    `).join('');
}

// ✅ FUNCIÓN MEJORADA CON DATA ATTRIBUTES
function getBotonesAdmin(producto) {
    // Obtener el rol del data attribute
    const userRol = obtenerRolUsuario();
    
    // Si no es admin, no mostrar botones
    if (userRol !== 'admin') {
        return '';
    }
    
    // Mostrar botón según estado del producto
    if (producto.Activo) {
        return `
            <button class="btn btn-sm btn-outline-danger" onclick="desactivarProducto(${producto.ID_Producto})" 
                    title="Desactivar producto">
                <i class="bi bi-pause-circle"></i>
            </button>
        `;
    } else {
        return `
            <button class="btn btn-sm btn-outline-success" onclick="activarProducto(${producto.ID_Producto})" 
                    title="Activar producto">
                <i class="bi bi-play-circle"></i>
            </button>
            <button class="btn btn-sm btn-outline-danger" onclick="eliminarProductoPermanente(${producto.ID_Producto})" 
                    title="Eliminar permanentemente">
                <i class="bi bi-trash"></i>
            </button>
        `;
    }
}

// ✅ FUNCIÓN NUEVA PARA ELIMINAR PERMANENTEMENTE
function eliminarProductoPermanente(id) {
    const producto = productos.find(p => p.ID_Producto === id);
    if (!producto) return;
    
    if (!confirm(`⚠️ ADVERTENCIA: ¿Estás completamente seguro de eliminar PERMANENTEMENTE el producto "${producto.Nombre}"?\n\nEsta acción NO se puede deshacer y solo es posible si el producto no tiene movimientos asociados.\n\nSi solo quieres deshabilitarlo temporalmente, usa "Desactivar" en su lugar.`)) {
        return;
    }
    
    fetch(`/api/inventario/productos/${id}`, {
        method: 'DELETE'
    })
    .then(response => {
        if (response.status === 403) {
            throw new Error('NO_PERMISSIONS');
        }
        if (response.status === 400) {
            return response.json().then(data => {
                throw new Error(data.error || 'No se puede eliminar el producto');
            });
        }
        if (!response.ok) throw new Error('Error al eliminar producto');
        return response.json();
    })
    .then(data => {
        mostrarExito(`Producto "${producto.Nombre}" eliminado permanentemente`);
        
        // Recargar productos
        cargarProductos();
        cargarEstadisticas();
    })
    .catch(error => {
        console.error('Error:', error);
        if (error.message === 'NO_PERMISSIONS') {
            mostrarError('No cuentas con los permisos para eliminar productos.');
        } else if (error.message.includes('movimientos asociados')) {
            mostrarError('❌ No se puede eliminar: Este producto tiene movimientos registrados. Solo puedes desactivarlo.');
        } else {
            mostrarError('Error al eliminar producto: ' + error.message);
        }
    });
}

function eliminarProductoPermanente(producto_id) {
    const producto = productos.find(p => p.ID_Producto === producto_id);
    if (!producto) return;
    
    if (!confirm(`¿Estás seguro de que quieres ELIMINAR PERMANENTEMENTE el producto "${producto.Nombre}"? Esta acción no se puede deshacer.`)) {
        return;
    }
    
    fetch(`/api/inventario/productos/${producto_id}`, {
        method: 'DELETE'
    })
    .then(response => {
        if (response.status === 403) {
            throw new Error('NO_PERMISSIONS');
        }
        if (!response.ok) throw new Error('Error al eliminar producto');
        return response.json();
    })
    .then(data => {
        mostrarExito(`Producto "${producto.Nombre}" eliminado permanentemente`);
        cargarProductos();
        cargarEstadisticas();
    })
    .catch(error => {
        console.error('Error:', error);
        if (error.message === 'NO_PERMISSIONS') {
            mostrarError('No cuentas con los permisos para eliminar productos.');
        } else {
            mostrarError('Error al eliminar producto: ' + error.message);
        }
    });
}

// ✅ FUNCIÓN ACTUALIZAR ESTADÍSTICAS - AGREGADA (FALTABA EN EL ORIGINAL)
function actualizarEstadisticas(productosData = productos) {
    const total = productosData.length;
    const activos = productosData.filter(p => p.Activo).length;
    const bajoStock = productosData.filter(p => p.Activo && p.Stock_Actual > 0 && p.Stock_Actual < p.Stock_Minimo).length;
    const sinStock = productosData.filter(p => p.Activo && p.Stock_Actual === 0).length;
    
    document.getElementById('totalProductos').textContent = total;
    document.getElementById('productosActivos').textContent = activos;
    document.getElementById('stockBajo').textContent = bajoStock;
    document.getElementById('sinStock').textContent = sinStock;
}

// ✅ FUNCIÓN CARGAR ESTADÍSTICAS - PARA USO INICIAL (FALTABA EN EL ORIGINAL)
function cargarEstadisticas() {
    // Si ya tenemos productos, usar esos datos
    if (productos.length > 0) {
        actualizarEstadisticas();
    } else {
        // Si no, hacer una petición específica para estadísticas
        fetch('/api/inventario/productos')
            .then(response => response.json())
            .then(data => {
                actualizarEstadisticas(data);
            })
            .catch(error => {
                console.error('Error cargando estadísticas:', error);
            });
    }
}

function getClaseStock(producto) {
    if (!producto.Activo) return '';
    if (producto.Stock_Actual === 0) return 'stock-critico';
    if (producto.Stock_Actual < producto.Stock_Minimo) return 'stock-bajo';
    return 'stock-normal';
}

function getBadgeStock(producto) {
    if (!producto.Activo) return 'bg-secondary';
    if (producto.Stock_Actual === 0) return 'bg-danger';
    if (producto.Stock_Actual < producto.Stock_Minimo) return 'bg-warning';
    return 'bg-success';
}

// ✅ FUNCIÓN MEJORADA - OCULTAR MODAL SI NO TIENE PERMISOS
function nuevoProducto() {
    // Verificar permisos antes de mostrar el modal
    if (!tienePermiso('crear')) {
        mostrarError('No cuentas con los permisos para crear productos.');
        return;
    }
    
    document.getElementById('tituloModalProducto').textContent = 'Nuevo Producto';
    document.getElementById('formProducto').reset();
    document.getElementById('productoId').value = '';
    document.getElementById('btnGuardarProducto').innerHTML = '<i class="bi bi-check-circle"></i> Crear Producto';
    
    // Mostrar modal
    new bootstrap.Modal(document.getElementById('modalProducto')).show();
}

function editarProducto(id) {
    // Verificar permisos antes de mostrar el modal
    if (!tienePermiso('editar')) {
        mostrarError('No cuentas con los permisos para editar productos.');
        return;
    }
    
    const producto = productos.find(p => p.ID_Producto === id);
    if (!producto) return;
    
    document.getElementById('tituloModalProducto').textContent = 'Editar Producto';
    document.getElementById('productoId').value = producto.ID_Producto;
    document.getElementById('codigo').value = producto.Codigo;
    document.getElementById('nombre').value = producto.Nombre;
    document.getElementById('categoria').value = producto.Categoria || '';
    document.getElementById('descripcion').value = producto.Descripcion || '';
    document.getElementById('unidad').value = producto.Unidad;
    document.getElementById('stockMinimo').value = producto.Stock_Minimo;
    document.getElementById('stockActual').value = producto.Stock_Actual;
    
    document.getElementById('btnGuardarProducto').innerHTML = '<i class="bi bi-check-circle"></i> Actualizar Producto';
    
    // Mostrar modal
    new bootstrap.Modal(document.getElementById('modalProducto')).show();
}

// ✅ FUNCIÓN MEJORADA CON MANEJO DE PERMISOS
function guardarProducto(event) {
    event.preventDefault();
    
    const productoId = document.getElementById('productoId').value;
    const esNuevo = !productoId;
    
    const datos = {
        Codigo: document.getElementById('codigo').value,
        Nombre: document.getElementById('nombre').value,
        Categoria: document.getElementById('categoria').value,
        Descripcion: document.getElementById('descripcion').value,
        Unidad: document.getElementById('unidad').value,
        Stock_Minimo: parseInt(document.getElementById('stockMinimo').value) || 0,
        Stock_Actual: parseInt(document.getElementById('stockActual').value) || 0
    };
    
    const btnGuardar = document.getElementById('btnGuardarProducto');
    btnGuardar.disabled = true;
    btnGuardar.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Guardando...';
    
    const url = esNuevo ? '/api/inventario/productos' : `/api/inventario/productos/${productoId}`;
    const method = esNuevo ? 'POST' : 'PUT';
    
    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(datos)
    })
    .then(response => {
        if (response.status === 403) {
            throw new Error('NO_PERMISSIONS');
        }
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        mostrarExito(esNuevo ? 'Producto creado exitosamente' : 'Producto actualizado exitosamente');
        bootstrap.Modal.getInstance(document.getElementById('modalProducto')).hide();
        cargarProductos();
        cargarEstadisticas();
        cargarAlertasStock();
    })
    .catch(error => {
        console.error('Error:', error);
        
        if (error.message === 'NO_PERMISSIONS') {
            mostrarError('No cuentas con los permisos necesarios para realizar esta acción. Contacta al administrador.');
        } else {
            mostrarError('Error al guardar producto: ' + error.message);
        }
    })
    .finally(() => {
        btnGuardar.disabled = false;
        btnGuardar.innerHTML = `<i class="bi bi-check-circle"></i> ${esNuevo ? 'Crear' : 'Actualizar'} Producto`;
    });
}

// ✅ FUNCIÓN MEJORADA - Mostrar productos inactivos después de desactivar
function desactivarProducto(id) {
    const producto = productos.find(p => p.ID_Producto === id);
    if (!producto) return;
    
    if (!confirm(`¿Estás seguro de que quieres desactivar el producto "${producto.Nombre}"? No podrá usarse en nuevos movimientos.`)) {
        return;
    }
    
    fetch(`/api/inventario/productos/${id}/desactivar`, {
        method: 'PUT'
    })
    .then(response => {
        if (response.status === 403) {
            throw new Error('NO_PERMISSIONS');
        }
        if (!response.ok) throw new Error('Error al desactivar producto');
        return response.json();
    })
    .then(data => {
        mostrarExito(`Producto "${producto.Nombre}" desactivado exitosamente`);
        
        // ✅ CAMBIAR EL FILTRO DE ESTADO A "TODOS" para ver productos inactivos
        document.getElementById('filtroEstado').value = '';
        
        // ✅ RECARGAR PRODUCTOS CON EL NUEVO FILTRO
        setTimeout(() => {
            cargarProductos();
            cargarEstadisticas();
        }, 100);
    })
    .catch(error => {
        console.error('Error:', error);
        if (error.message === 'NO_PERMISSIONS') {
            mostrarError('No cuentas con los permisos para desactivar productos.');
        } else {
            mostrarError('Error al desactivar producto: ' + error.message);
        }
    });
}

// ✅ FUNCIÓN MEJORADA PARA ACTIVAR PRODUCTO
function activarProducto(id) {
    const producto = productos.find(p => p.ID_Producto === id);
    if (!producto) return;
    
    if (!confirm(`¿Estás seguro de que quieres activar el producto "${producto.Nombre}"? Podrá usarse en nuevos movimientos.`)) {
        return;
    }
    
    fetch(`/api/inventario/productos/${id}/activar`, {
        method: 'PUT'
    })
    .then(response => {
        if (response.status === 403) {
            throw new Error('NO_PERMISSIONS');
        }
        if (!response.ok) throw new Error('Error al activar producto');
        return response.json();
    })
    .then(data => {
        mostrarExito(`Producto "${producto.Nombre}" activado exitosamente`);
        
        // ✅ MANTENER EL FILTRO ACTUAL (no cambiar a "Todos")
        cargarProductos();
        cargarEstadisticas();
    })
    .catch(error => {
        console.error('Error:', error);
        if (error.message === 'NO_PERMISSIONS') {
            mostrarError('No cuentas con los permisos para activar productos.');
        } else {
            mostrarError('Error al activar producto: ' + error.message);
        }
    });
}

// Gestión de Movimientos
function nuevoMovimiento(tipo, productoId = null) {
    // Verificar permisos antes de mostrar el modal
    if (!tienePermiso('movimientos')) {
        mostrarError('No cuentas con los permisos para registrar movimientos.');
        return;
    }
    
    document.getElementById('movimientoTipo').value = tipo;
    document.getElementById('tituloModalMovimiento').textContent = 
        tipo === 'entrada' ? 'Registrar Entrada' : 'Registrar Salida';
    
    document.getElementById('formMovimiento').reset();
    document.getElementById('responsable').value = '{{ session["user_nombre"] }}';
    
    // Mostrar/ocultar campos según tipo
    document.getElementById('campoProveedor').style.display = tipo === 'entrada' ? 'block' : 'none';
    document.getElementById('campoCliente').style.display = tipo === 'salida' ? 'block' : 'none';
    
    // Cargar productos en el select
    cargarProductosParaMovimientos(productoId);
    
    // Mostrar modal
    const modal = new bootstrap.Modal(document.getElementById('modalMovimiento'));
    modal.show();
    
    // Actualizar información de stock cuando se seleccione un producto
    document.getElementById('productoMovimiento').addEventListener('change', actualizarInfoStock);
}

function cargarProductosParaMovimientos(productoIdSeleccionado = null) {
    const select = document.getElementById('productoMovimiento');
    select.innerHTML = '<option value="">Seleccionar producto...</option>';
    
    productos.filter(p => p.Activo).forEach(producto => {
        const option = document.createElement('option');
        option.value = producto.ID_Producto;
        option.textContent = `${producto.Codigo} - ${producto.Nombre} (Stock: ${producto.Stock_Actual} ${producto.Unidad})`;
        option.selected = producto.ID_Producto === productoIdSeleccionado;
        select.appendChild(option);
    });
    
    if (productoIdSeleccionado) {
        actualizarInfoStock();
    }
}

function actualizarInfoStock() {
    const productoId = document.getElementById('productoMovimiento').value;
    const tipo = document.getElementById('movimientoTipo').value;
    const producto = productos.find(p => p.ID_Producto == productoId);
    
    const infoStock = document.getElementById('infoStock');
    
    if (!producto) {
        infoStock.innerHTML = '<i class="bi bi-info-circle"></i> Selecciona un producto para ver información del stock';
        return;
    }
    
    let mensaje = `<i class="bi bi-info-circle"></i> <strong>${escapeHtml(producto.Nombre)}</strong><br>`;
    mensaje += `Stock actual: <strong>${producto.Stock_Actual} ${producto.Unidad}</strong>`;
    mensaje += ` | Mínimo: <strong>${producto.Stock_Minimo} ${producto.Unidad}</strong>`;
    
    if (tipo === 'salida' && producto.Stock_Actual === 0) {
        mensaje += `<br><span class="text-danger"><i class="bi bi-exclamation-triangle"></i> Producto agotado</span>`;
    } else if (tipo === 'salida' && producto.Stock_Actual < producto.Stock_Minimo) {
        mensaje += `<br><span class="text-warning"><i class="bi bi-exclamation-triangle"></i> Stock bajo</span>`;
    }
    
    infoStock.innerHTML = mensaje;
}

// ✅ FUNCIÓN MEJORADA CON MANEJO DE PERMISOS
function guardarMovimiento(event) {
    event.preventDefault();
    
    const tipo = document.getElementById('movimientoTipo').value;
    const datos = {
        ID_Producto: parseInt(document.getElementById('productoMovimiento').value),
        Cantidad: parseInt(document.getElementById('cantidad').value),
        Referencia_Documento: document.getElementById('referencia').value,
        Responsable: document.getElementById('responsable').value
    };
    
    // Agregar proveedor o cliente según el tipo
    if (tipo === 'entrada') {
        const proveedorId = document.getElementById('proveedor').value;
        if (proveedorId) datos.ID_Proveedor = parseInt(proveedorId);
    } else {
        const clienteId = document.getElementById('cliente').value;
        if (clienteId) datos.ID_Cliente = parseInt(clienteId);
    }
    
    // Validaciones
    const producto = productos.find(p => p.ID_Producto == datos.ID_Producto);
    if (tipo === 'salida' && producto.Stock_Actual < datos.Cantidad) {
        mostrarError('No hay suficiente stock para realizar esta salida');
        return;
    }
    
    const btnGuardar = document.getElementById('btnGuardarMovimiento');
    btnGuardar.disabled = true;
    btnGuardar.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Registrando...';
    
    const url = tipo === 'entrada' ? '/api/inventario/entradas' : '/api/inventario/salidas';
    
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(datos)
    })
    .then(response => {
        if (response.status === 403) {
            throw new Error('NO_PERMISSIONS');
        }
        if (!response.ok) throw new Error('Error al registrar movimiento');
        return response.json();
    })
    .then(data => {
        mostrarExito(`Movimiento de ${tipo} registrado exitosamente`);
        bootstrap.Modal.getInstance(document.getElementById('modalMovimiento')).hide();
        cargarProductos();
        cargarEstadisticas();
        cargarAlertasStock();
    })
    .catch(error => {
        console.error('Error:', error);
        if (error.message === 'NO_PERMISSIONS') {
            mostrarError('No cuentas con los permisos para registrar movimientos.');
        } else {
            mostrarError('Error al registrar movimiento: ' + error.message);
        }
    })
    .finally(() => {
        btnGuardar.disabled = false;
        btnGuardar.innerHTML = '<i class="bi bi-check-circle"></i> Registrar Movimiento';
    });
}

// Historial de Movimientos
function verHistorial(productoId) {
    const producto = productos.find(p => p.ID_Producto === productoId);
    if (!producto) return;
    
    document.getElementById('modalHistorialLabel').textContent = `Historial - ${producto.Nombre}`;
    
    fetch(`/api/inventario/movimientos?producto_id=${productoId}&limit=50`)
        .then(response => {
            if (!response.ok) throw new Error('Error al cargar historial');
            return response.json();
        })
        .then(movimientos => {
            renderizarHistorial(movimientos);
            new bootstrap.Modal(document.getElementById('modalHistorial')).show();
        })
        .catch(error => {
            console.error('Error:', error);
            mostrarError('Error al cargar historial: ' + error.message);
        });
}

function renderizarHistorial(movimientos) {
    const tbody = document.getElementById('cuerpoHistorial');
    
    if (movimientos.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">No hay movimientos registrados</td></tr>';
        return;
    }
    
    tbody.innerHTML = movimientos.map(mov => `
        <tr>
            <td>${new Date(mov.Fecha).toLocaleString()}</td>
            <td>
                <span class="badge ${mov.Tipo === 'Entrada' ? 'bg-success' : 'bg-warning'}">
                    ${mov.Tipo}
                </span>
            </td>
            <td>${mov.producto_nombre || 'N/A'}</td>
            <td>
                <span class="fw-bold ${mov.Tipo === 'Entrada' ? 'text-success' : 'text-warning'}">
                    ${mov.Tipo === 'Entrada' ? '+' : '-'}${mov.Cantidad}
                </span>
            </td>
            <td>${mov.Referencia_Documento || '<span class="text-muted">N/A</span>'}</td>
            <td>${mov.Responsable}</td>
            <td>
                <small class="text-muted">${calcularStockResultante(movimientos, mov)}</small>
            </td>
        </tr>
    `).join('');
}

function calcularStockResultante(movimientos, movimientoActual) {
    // Calcular stock resultante después de este movimiento
    const index = movimientos.findIndex(m => m.ID_Movimiento === movimientoActual.ID_Movimiento);
    const movimientosHastaAhora = movimientos.slice(index);
    
    let stock = 0;
    movimientosHastaAhora.forEach(mov => {
        if (mov.Tipo === 'Entrada') {
            stock += mov.Cantidad;
        } else {
            stock -= mov.Cantidad;
        }
    });
    
    return stock;
}

// Funciones de utilidad
function cargarAlertasStock() {
    const alertas = productos.filter(p => 
        p.Activo && (p.Stock_Actual === 0 || p.Stock_Actual < p.Stock_Minimo)
    );
    
    const alertasDiv = document.getElementById('alertasStock');
    const listaAlertas = document.getElementById('listaAlertas');
    
    if (alertas.length === 0) {
        alertasDiv.style.display = 'none';
        return;
    }
    
    alertasDiv.style.display = 'block';
    listaAlertas.innerHTML = alertas.map(producto => `
        <div class="d-flex justify-content-between align-items-center mb-2">
            <div>
                <strong>${escapeHtml(producto.Nombre)}</strong> 
                <span class="badge ${producto.Stock_Actual === 0 ? 'bg-danger' : 'bg-warning'} ms-2">
                    ${producto.Stock_Actual === 0 ? 'AGOTADO' : `Stock bajo: ${producto.Stock_Actual}`}
                </span>
            </div>
            <button class="btn btn-sm btn-outline-primary" onclick="nuevoMovimiento('entrada', ${producto.ID_Producto})">
                <i class="bi bi-arrow-down-circle"></i> Reponer
            </button>
        </div>
    `).join('');
}

function cargarCategorias() {
    // Extraer categorías únicas de los productos
    const categoriasUnicas = [...new Set(productos.map(p => p.Categoria).filter(Boolean))];
    
    const select = document.getElementById('filtroCategoria');
    const datalist = document.getElementById('categoriasList');
    
    // Limpiar
    select.innerHTML = '<option value="">Todas las categorías</option>';
    datalist.innerHTML = '';
    
    categoriasUnicas.forEach(categoria => {
        // Agregar al select
        const option = document.createElement('option');
        option.value = categoria;
        option.textContent = categoria;
        select.appendChild(option);
        
        // Agregar al datalist
        const datalistOption = document.createElement('option');
        datalistOption.value = categoria;
        datalist.appendChild(datalistOption);
    });
}

function cargarProveedoresClientes() {
    // Cargar proveedores
    fetch('/api/inventario/proveedores')
        .then(response => response.json())
        .then(data => {
            proveedores = data;
            const select = document.getElementById('proveedor');
            select.innerHTML = '<option value="">Seleccionar proveedor...</option>';
            data.forEach(prov => {
                const option = document.createElement('option');
                option.value = prov.ID_Proveedor;
                option.textContent = prov.Nombre;
                select.appendChild(option);
            });
        })
        .catch(error => console.error('Error cargando proveedores:', error));
    
    // Cargar clientes
    fetch('/api/inventario/clientes')
        .then(response => response.json())
        .then(data => {
            clientes = data;
            const select = document.getElementById('cliente');
            select.innerHTML = '<option value="">Seleccionar cliente...</option>';
            data.forEach(cli => {
                const option = document.createElement('option');
                option.value = cli.ID_Cliente;
                option.textContent = cli.Nombre;
                select.appendChild(option);
            });
        })
        .catch(error => console.error('Error cargando clientes:', error));
}

function limpiarFiltros() {
    document.getElementById('buscarProducto').value = '';
    document.getElementById('filtroCategoria').value = '';
    document.getElementById('filtroEstado').value = ''; // ✅ Vacío = TODOS los productos
    document.getElementById('filtroStock').value = '';
    
    console.log('🧹 Filtros limpiados - Mostrando TODOS los productos');
    cargarProductos();
}

function exportarExcel() {
    // Implementación básica de exportación
    let csv = 'Código,Nombre,Categoría,Unidad,Stock Mínimo,Stock Actual,Estado\n';
    
    productos.forEach(producto => {
        csv += `"${producto.Codigo}","${producto.Nombre}","${producto.Categoria || ''}","${producto.Unidad}",${producto.Stock_Minimo},${producto.Stock_Actual},"${producto.Activo ? 'Activo' : 'Inactivo'}"\n`;
    });
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `inventario_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
}

// Utilidades
function mostrarCargandoTabla() {
    document.getElementById('cuerpoTabla').innerHTML = `
        <tr>
            <td colspan="8" class="text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Cargando...</span>
                </div>
                <p class="mt-2 text-muted">Cargando productos...</p>
            </td>
        </tr>
    `;
}

function mostrarExito(mensaje) {
    // Crear notificación de éxito
    const alert = document.createElement('div');
    alert.className = 'alert alert-success alert-dismissible fade show position-fixed';
    alert.style.cssText = 'top: 20px; right: 20px; z-index: 1060; min-width: 300px;';
    alert.innerHTML = `
        <i class="bi bi-check-circle"></i> ${mensaje}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alert);
    
    setTimeout(() => {
        if (alert.parentElement) alert.remove();
    }, 5000);
}

function mostrarError(mensaje) {
    // Crear notificación de error
    const alert = document.createElement('div');
    alert.className = 'alert alert-danger alert-dismissible fade show position-fixed';
    alert.style.cssText = 'top: 20px; right: 20px; z-index: 1060; min-width: 300px;';
    alert.innerHTML = `
        <i class="bi bi-exclamation-triangle"></i> ${mensaje}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alert);
    
    setTimeout(() => {
        if (alert.parentElement) alert.remove();
    }, 5000);
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Auto-actualización cada 30 segundos
setInterval(() => {
    if (!document.hidden) {
        cargarProductos();
        cargarAlertasStock();
    }
}, 30000);

// =============================================
// GESTIÓN DE CLIENTES Y PROVEEDORES
// =============================================

function gestionarClientesProveedores() {
    cargarClientes();
    cargarProveedores();
    new bootstrap.Modal(document.getElementById('modalGestionClientesProveedores')).show();
}

// ========== CLIENTES ==========

function nuevoCliente() {
    document.getElementById('tituloModalCliente').textContent = 'Nuevo Cliente';
    document.getElementById('formCliente').reset();
    document.getElementById('clienteId').value = '';
    document.getElementById('btnGuardarCliente').innerHTML = '<i class="bi bi-check-circle"></i> Crear Cliente';
    
    // Cerrar modal de gestión y abrir modal de cliente
    bootstrap.Modal.getInstance(document.getElementById('modalGestionClientesProveedores')).hide();
    new bootstrap.Modal(document.getElementById('modalCliente')).show();
}

function editarCliente(id) {
    const cliente = clientes.find(c => c.ID_Cliente === id);
    if (!cliente) return;
    
    document.getElementById('tituloModalCliente').textContent = 'Editar Cliente';
    document.getElementById('clienteId').value = cliente.ID_Cliente;
    document.getElementById('clienteNombre').value = cliente.Nombre;
    document.getElementById('clienteTelefono').value = cliente.Telefono || '';
    document.getElementById('clienteContacto').value = cliente.Contacto || '';
    document.getElementById('clienteEmail').value = cliente.Email || '';
    
    document.getElementById('btnGuardarCliente').innerHTML = '<i class="bi bi-check-circle"></i> Actualizar Cliente';
    
    // Cerrar modal de gestión y abrir modal de cliente
    bootstrap.Modal.getInstance(document.getElementById('modalGestionClientesProveedores')).hide();
    new bootstrap.Modal(document.getElementById('modalCliente')).show();
}

function guardarCliente(event) {
    event.preventDefault();
    
    const clienteId = document.getElementById('clienteId').value;
    const esNuevo = !clienteId;
    
    const datos = {
        Nombre: document.getElementById('clienteNombre').value,
        Telefono: document.getElementById('clienteTelefono').value,
        Contacto: document.getElementById('clienteContacto').value,
        Email: document.getElementById('clienteEmail').value
    };
    
    const btnGuardar = document.getElementById('btnGuardarCliente');
    btnGuardar.disabled = true;
    btnGuardar.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Guardando...';
    
    const url = '/api/inventario/clientes';
    const method = esNuevo ? 'POST' : 'PUT';
    
    // Para actualizar, necesitamos enviar el ID en la URL
    const urlFinal = esNuevo ? url : `${url}/${clienteId}`;
    
    fetch(urlFinal, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(datos)
    })
    .then(response => {
        if (!response.ok) throw new Error('Error al guardar cliente');
        return response.json();
    })
    .then(data => {
        mostrarExito(esNuevo ? 'Cliente creado exitosamente' : 'Cliente actualizado exitosamente');
        bootstrap.Modal.getInstance(document.getElementById('modalCliente')).hide();
        
        // Recargar lista de clientes y reabrir modal de gestión
        cargarClientes();
        cargarProveedoresClientes(); // Para actualizar los selects en movimientos
        new bootstrap.Modal(document.getElementById('modalGestionClientesProveedores')).show();
    })
    .catch(error => {
        console.error('Error:', error);
        mostrarError('Error al guardar cliente: ' + error.message);
    })
    .finally(() => {
        btnGuardar.disabled = false;
        btnGuardar.innerHTML = `<i class="bi bi-check-circle"></i> ${esNuevo ? 'Crear' : 'Actualizar'} Cliente`;
    });
}

function cargarClientes() {
    fetch('/api/inventario/clientes')
        .then(response => response.json())
        .then(data => {
            clientes = data;
            renderizarTablaClientes(data);
        })
        .catch(error => {
            console.error('Error cargando clientes:', error);
            document.getElementById('tablaClientesBody').innerHTML = 
                '<tr><td colspan="5" class="text-center text-muted">Error al cargar clientes</td></tr>';
        });
}

function renderizarTablaClientes(clientesData) {
    const tbody = document.getElementById('tablaClientesBody');
    
    if (clientesData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No hay clientes registrados</td></tr>';
        return;
    }
    
    tbody.innerHTML = clientesData.map(cliente => `
        <tr>
            <td>${escapeHtml(cliente.Nombre)}</td>
            <td>${cliente.Contacto ? escapeHtml(cliente.Contacto) : '<span class="text-muted">N/A</span>'}</td>
            <td>${cliente.Telefono ? escapeHtml(cliente.Telefono) : '<span class="text-muted">N/A</span>'}</td>
            <td>${cliente.Email ? escapeHtml(cliente.Email) : '<span class="text-muted">N/A</span>'}</td>
            <td>
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-primary" onclick="editarCliente(${cliente.ID_Cliente})" title="Editar">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-outline-danger" onclick="eliminarCliente(${cliente.ID_Cliente})" title="Eliminar">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

function eliminarCliente(id) {
    if (!confirm('¿Estás seguro de que quieres eliminar este cliente?')) {
        return;
    }
    
    fetch(`/api/inventario/clientes/${id}`, {
        method: 'DELETE'
    })
    .then(response => {
        if (!response.ok) throw new Error('Error al eliminar cliente');
        return response.json();
    })
    .then(data => {
        mostrarExito('Cliente eliminado exitosamente');
        cargarClientes();
        cargarProveedoresClientes(); // Actualizar selects
    })
    .catch(error => {
        console.error('Error:', error);
        mostrarError('Error al eliminar cliente: ' + error.message);
    });
}

// ========== PROVEEDORES ==========

function nuevoProveedor() {
    document.getElementById('tituloModalProveedor').textContent = 'Nuevo Proveedor';
    document.getElementById('formProveedor').reset();
    document.getElementById('proveedorId').value = '';
    document.getElementById('btnGuardarProveedor').innerHTML = '<i class="bi bi-check-circle"></i> Crear Proveedor';
    
    // Cerrar modal de gestión y abrir modal de proveedor
    bootstrap.Modal.getInstance(document.getElementById('modalGestionClientesProveedores')).hide();
    new bootstrap.Modal(document.getElementById('modalProveedor')).show();
}

function editarProveedor(id) {
    const proveedor = proveedores.find(p => p.ID_Proveedor === id);
    if (!proveedor) return;
    
    document.getElementById('tituloModalProveedor').textContent = 'Editar Proveedor';
    document.getElementById('proveedorId').value = proveedor.ID_Proveedor;
    document.getElementById('proveedorNombre').value = proveedor.Nombre;
    document.getElementById('proveedorTelefono').value = proveedor.Telefono || '';
    document.getElementById('proveedorContacto').value = proveedor.Contacto || '';
    document.getElementById('proveedorEmail').value = proveedor.Email || '';
    
    document.getElementById('btnGuardarProveedor').innerHTML = '<i class="bi bi-check-circle"></i> Actualizar Proveedor';
    
    // Cerrar modal de gestión y abrir modal de proveedor
    bootstrap.Modal.getInstance(document.getElementById('modalGestionClientesProveedores')).hide();
    new bootstrap.Modal(document.getElementById('modalProveedor')).show();
}

function guardarProveedor(event) {
    event.preventDefault();
    
    const proveedorId = document.getElementById('proveedorId').value;
    const esNuevo = !proveedorId;
    
    const datos = {
        Nombre: document.getElementById('proveedorNombre').value,
        Telefono: document.getElementById('proveedorTelefono').value,
        Contacto: document.getElementById('proveedorContacto').value,
        Email: document.getElementById('proveedorEmail').value
    };
    
    const btnGuardar = document.getElementById('btnGuardarProveedor');
    btnGuardar.disabled = true;
    btnGuardar.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Guardando...';
    
    const url = '/api/inventario/proveedores';
    const method = esNuevo ? 'POST' : 'PUT';
    
    // Para actualizar, necesitamos enviar el ID en la URL
    const urlFinal = esNuevo ? url : `${url}/${proveedorId}`;
    
    fetch(urlFinal, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(datos)
    })
    .then(response => {
        if (!response.ok) throw new Error('Error al guardar proveedor');
        return response.json();
    })
    .then(data => {
        mostrarExito(esNuevo ? 'Proveedor creado exitosamente' : 'Proveedor actualizado exitosamente');
        bootstrap.Modal.getInstance(document.getElementById('modalProveedor')).hide();
        
        // Recargar lista de proveedores y reabrir modal de gestión
        cargarProveedores();
        cargarProveedoresClientes(); // Para actualizar los selects en movimientos
        new bootstrap.Modal(document.getElementById('modalGestionClientesProveedores')).show();
    })
    .catch(error => {
        console.error('Error:', error);
        mostrarError('Error al guardar proveedor: ' + error.message);
    })
    .finally(() => {
        btnGuardar.disabled = false;
        btnGuardar.innerHTML = `<i class="bi bi-check-circle"></i> ${esNuevo ? 'Crear' : 'Actualizar'} Proveedor`;
    });
}

function cargarProveedores() {
    fetch('/api/inventario/proveedores')
        .then(response => response.json())
        .then(data => {
            proveedores = data;
            renderizarTablaProveedores(data);
        })
        .catch(error => {
            console.error('Error cargando proveedores:', error);
            document.getElementById('tablaProveedoresBody').innerHTML = 
                '<tr><td colspan="5" class="text-center text-muted">Error al cargar proveedores</td></tr>';
        });
}

function renderizarTablaProveedores(proveedoresData) {
    const tbody = document.getElementById('tablaProveedoresBody');
    
    if (proveedoresData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No hay proveedores registrados</td></tr>';
        return;
    }
    
    tbody.innerHTML = proveedoresData.map(proveedor => `
        <tr>
            <td>${escapeHtml(proveedor.Nombre)}</td>
            <td>${proveedor.Contacto ? escapeHtml(proveedor.Contacto) : '<span class="text-muted">N/A</span>'}</td>
            <td>${proveedor.Telefono ? escapeHtml(proveedor.Telefono) : '<span class="text-muted">N/A</span>'}</td>
            <td>${proveedor.Email ? escapeHtml(proveedor.Email) : '<span class="text-muted">N/A</span>'}</td>
            <td>
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-primary" onclick="editarProveedor(${proveedor.ID_Proveedor})" title="Editar">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-outline-danger" onclick="eliminarProveedor(${proveedor.ID_Proveedor})" title="Eliminar">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

function eliminarProveedor(id) {
    if (!confirm('¿Estás seguro de que quieres eliminar este proveedor?')) {
        return;
    }
    
    fetch(`/api/inventario/proveedores/${id}`, {
        method: 'DELETE'
    })
    .then(response => {
        if (!response.ok) throw new Error('Error al eliminar proveedor');
        return response.json();
    })
    .then(data => {
        mostrarExito('Proveedor eliminado exitosamente');
        cargarProveedores();
        cargarProveedoresClientes(); // Actualizar selects
    })
    .catch(error => {
        console.error('Error:', error);
        mostrarError('Error al eliminar proveedor: ' + error.message);
    });
}

// static/js/inventory.js - AGREGAR estas funciones

function mostrarNotificacionEnvio(correosEnviados) {
    if (correosEnviados && correosEnviados.length > 0) {
        const exitosos = correosEnviados.filter(c => c[1]).length;
        const fallidos = correosEnviados.filter(c => !c[1]).length;
        
        let mensaje = `📧 Notificaciones enviadas: ${exitosos} exitosas`;
        if (fallidos > 0) {
            mensaje += `, ${fallidos} fallidas`;
        }
        
        mostrarExito(mensaje);
    }
}

// Modificar la función guardarProducto para manejar la respuesta
function guardarProducto(event) {
    event.preventDefault();
    
    const productoId = document.getElementById('productoId').value;
    const esNuevo = !productoId;
    
    const datos = {
        Codigo: document.getElementById('codigo').value,
        Nombre: document.getElementById('nombre').value,
        Categoria: document.getElementById('categoria').value,
        Descripcion: document.getElementById('descripcion').value,
        Unidad: document.getElementById('unidad').value,
        Stock_Minimo: parseInt(document.getElementById('stockMinimo').value) || 0,
        Stock_Actual: parseInt(document.getElementById('stockActual').value) || 0
    };
    
    const btnGuardar = document.getElementById('btnGuardarProducto');
    btnGuardar.disabled = true;
    btnGuardar.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Guardando...';
    
    const url = esNuevo ? '/api/inventario/productos' : `/api/inventario/productos/${productoId}`;
    const method = esNuevo ? 'POST' : 'PUT';
    
    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(datos)
    })
    .then(response => {
        if (response.status === 403) {
            throw new Error('NO_PERMISSIONS');
        }
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        mostrarExito(esNuevo ? 'Producto creado exitosamente' : 'Producto actualizado exitosamente');
        
        // 🔔 Mostrar información de notificaciones si está disponible
        if (data.notificaciones) {
            setTimeout(() => {
                mostrarNotificacionEnvio(data.notificaciones);
            }, 1000);
        }
        
        bootstrap.Modal.getInstance(document.getElementById('modalProducto')).hide();
        cargarProductos();
        cargarEstadisticas();
        cargarAlertasStock();
    })
    .catch(error => {
        console.error('Error:', error);
        
        if (error.message === 'NO_PERMISSIONS') {
            mostrarError('No cuentas con los permisos necesarios para realizar esta acción. Contacta al administrador.');
        } else {
            mostrarError('Error al guardar producto: ' + error.message);
        }
    })
    .finally(() => {
        btnGuardar.disabled = false;
        btnGuardar.innerHTML = `<i class="bi bi-check-circle"></i> ${esNuevo ? 'Crear' : 'Actualizar'} Producto`;
    });
}

// ========== FUNCIÓN MEJORADA PARA CARGAR PROVEEDORES Y CLIENTES ==========

function cargarProveedoresClientes() {
    // Cargar proveedores
    fetch('/api/inventario/proveedores')
        .then(response => response.json())
        .then(data => {
            proveedores = data;
            const select = document.getElementById('proveedor');
            select.innerHTML = '<option value="">Seleccionar proveedor...</option>';
            data.forEach(prov => {
                const option = document.createElement('option');
                option.value = prov.ID_Proveedor;
                option.textContent = prov.Nombre;
                select.appendChild(option);
            });
        })
        .catch(error => console.error('Error cargando proveedores:', error));
    
    // Cargar clientes
    fetch('/api/inventario/clientes')
        .then(response => response.json())
        .then(data => {
            clientes = data;
            const select = document.getElementById('cliente');
            select.innerHTML = '<option value="">Seleccionar cliente...</option>';
            data.forEach(cli => {
                const option = document.createElement('option');
                option.value = cli.ID_Cliente;
                option.textContent = cli.Nombre;
                select.appendChild(option);
            });
        })
        .catch(error => console.error('Error cargando clientes:', error));
}