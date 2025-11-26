from flask import render_template, request, redirect, url_for, flash, jsonify
from models import Usuario

class UsuarioController:
    @staticmethod
    def listar_usuarios():
        # Obtener parámetros de filtro
        nombre_filtro = request.args.get('nombre', '')
        rol_filtro = request.args.get('rol', '')
        
        if nombre_filtro or rol_filtro:
            usuarios = Usuario.obtener_con_filtros(
                nombre=nombre_filtro if nombre_filtro else None,
                rol=rol_filtro if rol_filtro else None
            )
        else:
            usuarios = Usuario.obtener_todos()
            
        return render_template('listar_usuarios.html', usuarios=usuarios)
    
    @staticmethod
    def nuevo_usuario():
        if request.method == 'POST':
            nombre = request.form['nombre']
            email = request.form['email']
            password = request.form['password']
            rol = request.form['rol']
            
            # Validaciones básicas
            if not all([nombre, email, password, rol]):
                flash('Todos los campos son obligatorios', 'error')
                return render_template('nuevo_usuario.html')
            
            if Usuario.email_existe(email):
                flash('El email ya está registrado', 'error')
                return render_template('nuevo_usuario.html')
            
            try:
                Usuario.crear(nombre, email, password, rol)
                flash('Usuario creado exitosamente', 'success')
                return redirect(url_for('listar_usuarios'))
            except ValueError as e:
                flash(str(e), 'error')
        
        return render_template('nuevo_usuario.html')
    
    @staticmethod
    def editar_usuario(id):
        usuario = Usuario.obtener_por_id(id)
        if not usuario:
            flash('Usuario no encontrado', 'error')
            return redirect(url_for('listar_usuarios'))
        
        if request.method == 'POST':
            nombre = request.form['nombre']
            email = request.form['email']
            rol = request.form['rol']
            
            if not all([nombre, email, rol]):
                flash('Todos los campos son obligatorios', 'error')
                return render_template('editar_usuario.html', usuario=usuario)
            
            try:
                Usuario.actualizar(id, nombre, email, rol)
                flash('Usuario actualizado exitosamente', 'success')
                return redirect(url_for('listar_usuarios'))
            except ValueError as e:
                flash(str(e), 'error')
                return render_template('editar_usuario.html', usuario=usuario)
        
        return render_template('editar_usuario.html', usuario=usuario)
    
    @staticmethod
    def eliminar_usuario(id):
        try:
            Usuario.eliminar(id)
            flash('Usuario eliminado exitosamente', 'success')
        except ValueError as e:
            flash(str(e), 'error')
        
        return redirect(url_for('listar_usuarios'))