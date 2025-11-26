import os
import io
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics import renderPDF
import base64

class ReportGenerator:
    
    @staticmethod
    def generate_excel_report(productos, movimientos, filename=None):
        """Generar reporte en Excel profesional"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reporte_inventario_{timestamp}.xlsx"
        
        # Crear Excel writer
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            
            # Hoja 1: Resumen de Productos
            df_productos = pd.DataFrame([{
                'Código': p['Codigo'],
                'Nombre': p['Nombre'],
                'Categoría': p['Categoria'] or 'Sin categoría',
                'Unidad': p['Unidad'],
                'Stock Mínimo': p['Stock_Minimo'],
                'Stock Actual': p['Stock_Actual'],
                'Estado': 'Activo' if p['Activo'] else 'Inactivo',
                'Diferencia': p['Stock_Actual'] - p['Stock_Minimo'],
                'Alerta': 'CRÍTICO' if p['Stock_Actual'] == 0 else 'BAJO' if p['Stock_Actual'] < p['Stock_Minimo'] else 'NORMAL'
            } for p in productos])
            
            # Formatear hoja de productos
            df_productos.to_excel(writer, sheet_name='Resumen Productos', index=False)
            worksheet = writer.sheets['Resumen Productos']
            
            # Ajustar anchos de columna
            column_widths = {'A': 15, 'B': 30, 'C': 20, 'D': 12, 'E': 15, 'F': 15, 'G': 12, 'H': 15, 'I': 12}
            for col, width in column_widths.items():
                worksheet.column_dimensions[col].width = width
            
            # Hoja 2: Movimientos
            if movimientos:
                df_movimientos = pd.DataFrame([{
                    'Fecha': m['Fecha'].split('T')[0] if 'T' in str(m['Fecha']) else m['Fecha'],
                    'Tipo': m['Tipo'],
                    'Producto': m.get('producto_nombre', 'N/A'),
                    'Cantidad': m['Cantidad'],
                    'Referencia': m.get('Referencia_Documento', 'N/A'),
                    'Responsable': m['Responsable']
                } for m in movimientos])
                
                df_movimientos.to_excel(writer, sheet_name='Movimientos', index=False)
                worksheet = writer.sheets['Movimientos']
                
                # Ajustar anchos
                mov_widths = {'A': 12, 'B': 10, 'C': 25, 'D': 12, 'E': 20, 'F': 20}
                for col, width in mov_widths.items():
                    worksheet.column_dimensions[col].width = width
            
            # Hoja 3: Estadísticas
            stats_data = {
                'Métrica': [
                    'Total Productos',
                    'Productos Activos',
                    'Productos Inactivos',
                    'Stock Bajo',
                    'Sin Stock',
                    'Stock Normal'
                ],
                'Valor': [
                    len(productos),
                    len([p for p in productos if p['Activo']]),
                    len([p for p in productos if not p['Activo']]),
                    len([p for p in productos if p['Activo'] and p['Stock_Actual'] < p['Stock_Minimo'] and p['Stock_Actual'] > 0]),
                    len([p for p in productos if p['Activo'] and p['Stock_Actual'] == 0]),
                    len([p for p in productos if p['Activo'] and p['Stock_Actual'] >= p['Stock_Minimo']])
                ]
            }
            
            df_stats = pd.DataFrame(stats_data)
            df_stats.to_excel(writer, sheet_name='Estadísticas', index=False)
        
        output.seek(0)
        return output.getvalue(), filename
    
    @staticmethod
    def generate_pdf_report(productos, movimientos, filename=None):
        """Generar reporte PDF profesional con gráficas"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reporte_inventario_{timestamp}.pdf"
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch)
        elements = []
        styles = getSampleStyleSheet()
        
        # Estilo personalizado para títulos
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            textColor=colors.HexColor('#2c3e50'),
            alignment=1  # Centrado
        )
        
        # Título del reporte
        title = Paragraph("REPORTE DE INVENTARIO - SISTEMA DE SEGURIDAD", title_style)
        elements.append(title)
        
        # Fecha de generación
        date_style = ParagraphStyle(
            'DateStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.gray,
            alignment=1
        )
        date_text = Paragraph(f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M')}", date_style)
        elements.append(date_text)
        elements.append(Spacer(1, 20))
        
        # Estadísticas rápidas
        stats_style = ParagraphStyle(
            'StatsStyle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#34495e'),
            backColor=colors.HexColor('#ecf0f1'),
            borderPadding=10,
            spaceAfter=12
        )
        
        total_activos = len([p for p in productos if p['Activo']])
        stock_bajo = len([p for p in productos if p['Activo'] and p['Stock_Actual'] < p['Stock_Minimo'] and p['Stock_Actual'] > 0])
        sin_stock = len([p for p in productos if p['Activo'] and p['Stock_Actual'] == 0])
        
        stats_text = f"""
        <b>RESUMEN EJECUTIVO:</b><br/>
        • Productos activos: {total_activos}<br/>
        • Productos con stock bajo: {stock_bajo}<br/>
        • Productos sin stock: {sin_stock}<br/>
        • Total de movimientos analizados: {len(movimientos) if movimientos else 0}
        """
        elements.append(Paragraph(stats_text, stats_style))
        elements.append(Spacer(1, 25))
        
        # Gráfica de estado de stock
        elements.append(Paragraph("<b>DISTRIBUCIÓN DE ESTADO DE STOCK</b>", styles['Heading2']))
        elements.append(Spacer(1, 10))
        
        # Crear gráfica de pie
        drawing = Drawing(400, 200)
        pie = Pie()
        pie.x = 150
        pie.y = 50
        pie.width = 150
        pie.height = 150
        
        # Datos para la gráfica
        normal_count = len([p for p in productos if p['Activo'] and p['Stock_Actual'] >= p['Stock_Minimo']])
        bajo_count = len([p for p in productos if p['Activo'] and p['Stock_Actual'] < p['Stock_Minimo'] and p['Stock_Actual'] > 0])
        critico_count = len([p for p in productos if p['Activo'] and p['Stock_Actual'] == 0])
        inactivo_count = len([p for p in productos if not p['Activo']])
        
        pie.data = [normal_count, bajo_count, critico_count, inactivo_count]
        pie.labels = [f'Normal: {normal_count}', f'Bajo: {bajo_count}', 
                     f'Crítico: {critico_count}', f'Inactivos: {inactivo_count}']
        pie.slices.strokeWidth = 0.5
        pie.slices[0].fillColor = colors.green
        pie.slices[1].fillColor = colors.orange
        pie.slices[2].fillColor = colors.red
        pie.slices[3].fillColor = colors.gray
        
        drawing.add(pie)
        elements.append(drawing)
        elements.append(Spacer(1, 30))
        
        # Tabla de productos con stock bajo
        productos_bajo_stock = [p for p in productos if p['Activo'] and 
                               (p['Stock_Actual'] < p['Stock_Minimo'] or p['Stock_Actual'] == 0)]
        
        if productos_bajo_stock:
            elements.append(Paragraph("<b>PRODUCTOS QUE REQUIEREN ATENCIÓN</b>", styles['Heading2']))
            elements.append(Spacer(1, 10))
            
            # Preparar datos para la tabla
            table_data = [['Código', 'Nombre', 'Stock Actual', 'Stock Mínimo', 'Diferencia', 'Alerta']]
            
            for producto in productos_bajo_stock[:10]:  # Máximo 10 productos
                diferencia = producto['Stock_Actual'] - producto['Stock_Minimo']
                alerta = 'CRÍTICO' if producto['Stock_Actual'] == 0 else 'BAJO'
                table_data.append([
                    producto['Codigo'],
                    producto['Nombre'][:30] + '...' if len(producto['Nombre']) > 30 else producto['Nombre'],
                    str(producto['Stock_Actual']),
                    str(producto['Stock_Minimo']),
                    str(diferencia),
                    alerta
                ])
            
            # Crear tabla
            table = Table(table_data, colWidths=[80, 150, 70, 70, 70, 60])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
            ]))
            
            elements.append(table)
            elements.append(Spacer(1, 20))
        
        # Últimos movimientos
        if movimientos:
            elements.append(Paragraph("<b>ÚLTIMOS MOVIMIENTOS</b>", styles['Heading2']))
            elements.append(Spacer(1, 10))
            
            mov_data = [['Fecha', 'Tipo', 'Producto', 'Cantidad', 'Responsable']]
            
            for mov in movimientos[:15]:  # Últimos 15 movimientos
                fecha = mov['Fecha'].split('T')[0] if 'T' in str(mov['Fecha']) else mov['Fecha']
                mov_data.append([
                    fecha,
                    mov['Tipo'],
                    mov.get('producto_nombre', 'N/A')[:25] + '...' if len(mov.get('producto_nombre', '')) > 25 else mov.get('producto_nombre', 'N/A'),
                    str(mov['Cantidad']),
                    mov['Responsable'][:15] + '...' if len(mov['Responsable']) > 15 else mov['Responsable']
                ])
            
            mov_table = Table(mov_data, colWidths=[60, 50, 120, 50, 80])
            mov_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ffffff')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
            ]))
            
            elements.append(mov_table)
        
        # Pie de página
        elements.append(Spacer(1, 30))
        footer_style = ParagraphStyle(
            'FooterStyle',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.gray,
            alignment=1
        )
        footer = Paragraph("Sistema de Seguridad - Reporte generado automáticamente", footer_style)
        elements.append(footer)
        
        # Generar PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue(), filename

    @staticmethod
    def create_stock_chart_image(productos):
        """Crear gráfica de stock para incluir en reportes"""
        plt.figure(figsize=(10, 6))
        
        # Preparar datos
        productos_activos = [p for p in productos if p['Activo']][:10]  # Top 10 productos
        
        nombres = [p['Nombre'][:15] + '...' if len(p['Nombre']) > 15 else p['Nombre'] for p in productos_activos]
        stock_actual = [p['Stock_Actual'] for p in productos_activos]
        stock_minimo = [p['Stock_Minimo'] for p in productos_activos]
        
        x = range(len(nombres))
        
        plt.bar(x, stock_actual, width=0.4, label='Stock Actual', color='skyblue', align='center')
        plt.bar([i + 0.4 for i in x], stock_minimo, width=0.4, label='Stock Mínimo', color='orange', align='center')
        
        plt.xlabel('Productos')
        plt.ylabel('Cantidad')
        plt.title('Comparación: Stock Actual vs Stock Mínimo')
        plt.xticks([i + 0.2 for i in x], nombres, rotation=45, ha='right')
        plt.legend()
        plt.tight_layout()
        
        # Guardar en buffer
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()
        
        return img_buffer