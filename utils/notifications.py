# utils/notifications.py - MODIFICAR para usar contexto de aplicación

from auth.utils import enviar_notificacion_inventario, obtener_correos_administradores, obtener_correos_editores
from datetime import datetime

class NotificacionesInventario:
    
    @staticmethod
    def notificar_nuevo_producto(producto, usuario_creador):
        """Notificar creación de nuevo producto"""
        try:
            asunto = "🆕 Nuevo Producto Registrado - Sistema de Inventario"
            
            cuerpo = f"""
            <div class="success">
                <h3>Nuevo Producto Registrado</h3>
                <p><strong>Producto:</strong> {producto['Nombre']} ({producto['Codigo']})</p>
                <p><strong>Categoría:</strong> {producto.get('Categoria', 'No especificada')}</p>
                <p><strong>Unidad:</strong> {producto['Unidad']}</p>
                <p><strong>Stock Mínimo:</strong> {producto.get('Stock_Minimo', 0)}</p>
                <p><strong>Stock Inicial:</strong> {producto.get('Stock_Actual', 0)}</p>
                <p><strong>Registrado por:</strong> {usuario_creador}</p>
                <p><strong>Fecha:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            </div>
            """
            
            # Enviar a administradores y editores
            destinatarios = obtener_correos_editores()
            resultados = []
            
            for destinatario in destinatarios:
                exito = enviar_notificacion_inventario(destinatario, asunto, cuerpo, "nuevo_producto")
                resultados.append((destinatario, exito))
            
            return resultados
        except Exception as e:
            print(f"❌ Error en notificación nuevo producto: {e}")
            return []
    
    @staticmethod
    def notificar_entrada_inventario(movimiento, producto, usuario_responsable, nuevo_stock):
        """Notificar entrada de inventario"""
        try:
            asunto = "📥 Entrada de Inventario Registrada - Sistema de Inventario"
            
            cuerpo = f"""
            <div class="success">
                <h3>Entrada de Inventario Registrada</h3>
                <p><strong>Producto:</strong> {producto['Nombre']} ({producto['Codigo']})</p>
                <p><strong>Cantidad Ingresada:</strong> +{movimiento['Cantidad']} {producto['Unidad']}</p>
                <p><strong>Stock Anterior:</strong> {producto['Stock_Actual'] - movimiento['Cantidad']} {producto['Unidad']}</p>
                <p><strong>Nuevo Stock:</strong> {nuevo_stock} {producto['Unidad']}</p>
                <p><strong>Referencia:</strong> {movimiento.get('Referencia_Documento', 'N/A')}</p>
                <p><strong>Responsable:</strong> {usuario_responsable}</p>
                <p><strong>Fecha:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            </div>
            """
            
            # Enviar a administradores y editores
            destinatarios = obtener_correos_editores()
            resultados = []
            
            for destinatario in destinatarios:
                exito = enviar_notificacion_inventario(destinatario, asunto, cuerpo, "entrada_inventario")
                resultados.append((destinatario, exito))
            
            return resultados
        except Exception as e:
            print(f"❌ Error en notificación entrada inventario: {e}")
            return []
    
    @staticmethod
    def notificar_salida_inventario(movimiento, producto, usuario_responsable, nuevo_stock):
        """Notificar salida de inventario"""
        try:
            asunto = "📤 Salida de Inventario Registrada - Sistema de Inventario"
            
            # Verificar si el stock quedó bajo después de la salida
            stock_bajo = nuevo_stock < producto.get('Stock_Minimo', 0)
            alerta_stock = ""
            
            if stock_bajo:
                alerta_stock = f"""
                <div class="warning">
                    <p>⚠️ <strong>ALERTA:</strong> Stock bajo después de esta salida</p>
                    <p>Stock actual ({nuevo_stock}) está por debajo del mínimo ({producto.get('Stock_Minimo', 0)})</p>
                </div>
                """
            
            cuerpo = f"""
            <div class="alert">
                <h3>Salida de Inventario Registrada</h3>
                <p><strong>Producto:</strong> {producto['Nombre']} ({producto['Codigo']})</p>
                <p><strong>Cantidad Retirada:</strong> -{movimiento['Cantidad']} {producto['Unidad']}</p>
                <p><strong>Stock Anterior:</strong> {producto['Stock_Actual'] + movimiento['Cantidad']} {producto['Unidad']}</p>
                <p><strong>Nuevo Stock:</strong> {nuevo_stock} {producto['Unidad']}</p>
                <p><strong>Referencia:</strong> {movimiento.get('Referencia_Documento', 'N/A')}</p>
                <p><strong>Responsable:</strong> {usuario_responsable}</p>
                <p><strong>Fecha:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            </div>
            {alerta_stock}
            """
            
            # Enviar a administradores y editores
            destinatarios = obtener_correos_editores()
            resultados = []
            
            for destinatario in destinatarios:
                exito = enviar_notificacion_inventario(destinatario, asunto, cuerpo, "salida_inventario")
                resultados.append((destinatario, exito))
            
            return resultados
        except Exception as e:
            print(f"❌ Error en notificación salida inventario: {e}")
            return []
    
    @staticmethod
    def notificar_stock_agotado(producto):
        """Notificar cuando un producto se agota"""
        try:
            asunto = "🚨 ALERTA: Producto Agotado - Sistema de Inventario"
            
            cuerpo = f"""
            <div class="danger">
                <h3>🚨 PRODUCTO AGOTADO</h3>
                <p><strong>Producto:</strong> {producto['Nombre']} ({producto['Codigo']})</p>
                <p><strong>Categoría:</strong> {producto.get('Categoria', 'No especificada')}</p>
                <p><strong>Stock Actual:</strong> 0 {producto['Unidad']}</p>
                <p><strong>Stock Mínimo:</strong> {producto.get('Stock_Minimo', 0)} {producto['Unidad']}</p>
                <p><strong>Urgencia:</strong> ALTA - Se requiere reposición inmediata</p>
                <p><strong>Fecha de Alerta:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            </div>
            
            <div class="alert">
                <h4>📋 Acción Requerida:</h4>
                <ul>
                    <li>Contactar al proveedor para reposición</li>
                    <li>Verificar pedidos pendientes</li>
                    <li>Actualizar fecha estimada de reposición</li>
                </ul>
            </div>
            """
            
            # Enviar a todos los administradores y editores
            destinatarios = obtener_correos_editores()
            resultados = []
            
            for destinatario in destinatarios:
                exito = enviar_notificacion_inventario(destinatario, asunto, cuerpo, "stock_agotado")
                resultados.append((destinatario, exito))
            
            return resultados
        except Exception as e:
            print(f"❌ Error en notificación stock agotado: {e}")
            return []
    
    @staticmethod
    def notificar_stock_bajo(producto):
        """Notificar cuando un producto está bajo de stock"""
        try:
            asunto = "⚠️ Alerta: Stock Bajo - Sistema de Inventario"
            
            diferencia = producto.get('Stock_Minimo', 0) - producto['Stock_Actual']
            
            cuerpo = f"""
            <div class="warning">
                <h3>⚠️ STOCK BAJO</h3>
                <p><strong>Producto:</strong> {producto['Nombre']} ({producto['Codigo']})</p>
                <p><strong>Categoría:</strong> {producto.get('Categoria', 'No especificada')}</p>
                <p><strong>Stock Actual:</strong> {producto['Stock_Actual']} {producto['Unidad']}</p>
                <p><strong>Stock Mínimo:</strong> {producto.get('Stock_Minimo', 0)} {producto['Unidad']}</p>
                <p><strong>Faltan:</strong> {diferencia} {producto['Unidad']} para alcanzar el mínimo</p>
                <p><strong>Fecha de Alerta:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            </div>
            
            <div class="alert">
                <h4>💡 Recomendación:</h4>
                <p>Considerar realizar un pedido de reposición pronto.</p>
            </div>
            """
            
            # Enviar a administradores y editores
            destinatarios = obtener_correos_editores()
            resultados = []
            
            for destinatario in destinatarios:
                exito = enviar_notificacion_inventario(destinatario, asunto, cuerpo, "stock_bajo")
                resultados.append((destinatario, exito))
            
            return resultados
        except Exception as e:
            print(f"❌ Error en notificación stock bajo: {e}")
            return []