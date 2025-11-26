from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from auth.decorators import login_required, twofa_required, admin_required, editor_required
from models.user import Usuario

users_bp = Blueprint('users', __name__)

@users_bp.route('/usuarios')
@login_required
@twofa_required
def listar_usuarios():
    try:
        nombre_filtro = request.args.get('nombre', '')
        rol_filtro = request.args.get('rol', '')
        
        if nombre_filtro or rol_filtro:
            usuarios = Usuario.obtener_con_filtros(
                nombre=nombre_filtro if nombre_filtro else None,
                rol=rol_filtro if rol_filtro else None
            )
        else:
            usuarios = Usuario.obtener_todos()
            
        return render_template('listar_usuarios.html', 
                             usuarios=usuarios, 
                             user_rol=session.get('user_rol', 'lector'))
    except Exception as e:
        flash(f'Error al obtener usuarios: {str(e)}', 'error')
        return render_template('listar_usuarios.html', 
                             usuarios=[], 
                             user_rol=session.get('user_rol', 'lector'))

@users_bp.route('/usuarios/nuevo', methods=['GET', 'POST'])
@login_required
@twofa_required
@admin_required
def nuevo_usuario():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        password = request.form['password']
        rol = request.form['rol']
        
        from utils.validation import validar_nombre, validar_password, validar_email
        
        if not all([nombre, email, password, rol]):
            flash('Todos los campos son obligatorios', 'error')
            return render_template('nuevo_usuario.html')
        
        es_valido, mensaje_error = validar_nombre(nombre)
        if not es_valido:
            flash(mensaje_error, 'error')
            return render_template('nuevo_usuario.html')
        
        if not validar_email(email):
            flash('Por favor ingresa un email válido', 'error')
            return render_template('nuevo_usuario.html')
        
        es_valida, mensaje_error = validar_password(password)
        if not es_valida:
            flash(mensaje_error, 'error')
            return render_template('nuevo_usuario.html')
        
        try:
            Usuario.crear(nombre, email, password, rol)
            flash('Usuario creado exitosamente', 'success')
            return redirect(url_for('users.listar_usuarios'))
        except ValueError as e:
            flash(str(e), 'error')
        except Exception as e:
            flash(f'Error al crear usuario: {str(e)}', 'error')
    
    return render_template('nuevo_usuario.html')

@users_bp.route('/usuarios/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@twofa_required
@editor_required
def editar_usuario(id):
    try:
        usuario = Usuario.obtener_por_id(id)
        if not usuario:
            flash('Usuario no encontrado', 'error')
            return redirect(url_for('users.listar_usuarios'))
        
        if session['user_rol'] == 'editor':
            if usuario.rol == 'admin':
                flash('No tienes permisos para editar administradores', 'error')
                return redirect(url_for('users.listar_usuarios'))
        
        if request.method == 'POST':
            nombre = request.form['nombre']
            email = request.form['email']
            rol = request.form['rol']
            nueva_password = request.form.get('nueva_password', '')
            
            if session['user_rol'] == 'editor':
                rol = usuario.rol
            
            if not all([nombre, email, rol]):
                flash('Todos los campos son obligatorios', 'error')
                return render_template('editar_usuario.html', usuario=usuario, user_rol=session['user_rol'])
            
            from utils.validation import validar_nombre, validar_password, validar_email
            
            es_valido, mensaje_error = validar_nombre(nombre)
            if not es_valido:
                flash(mensaje_error, 'error')
                return render_template('editar_usuario.html', usuario=usuario, user_rol=session['user_rol'])
            
            if not validar_email(email):
                flash('Por favor ingresa un email válido', 'error')
                return render_template('editar_usuario.html', usuario=usuario, user_rol=session['user_rol'])
            
            if nueva_password:
                es_valida, mensaje_error = validar_password(nueva_password)
                if not es_valida:
                    flash(mensaje_error, 'error')
                    return render_template('editar_usuario.html', usuario=usuario, user_rol=session['user_rol'])
            
            try:
                if nueva_password:
                    Usuario.actualizar(id, nombre, email, rol, nueva_password)
                    flash('Usuario y contraseña actualizados exitosamente', 'success')
                else:
                    Usuario.actualizar(id, nombre, email, rol)
                    flash('Usuario actualizado exitosamente', 'success')
                
                return redirect(url_for('users.listar_usuarios'))
            except ValueError as e:
                flash(str(e), 'error')
            except Exception as e:
                flash(f'Error al actualizar usuario: {str(e)}', 'error')
            
            return render_template('editar_usuario.html', usuario=usuario, user_rol=session['user_rol'])
        
        return render_template('editar_usuario.html', usuario=usuario, user_rol=session['user_rol'])
        
    except Exception as e:
        flash(f'Error al cargar usuario: {str(e)}', 'error')
        return redirect(url_for('users.listar_usuarios'))

@users_bp.route('/usuarios/eliminar/<int:id>', methods=['POST'])
@login_required
@twofa_required
@admin_required
def eliminar_usuario(id):
    try:
        if id == session['user_id']:
            flash('No puedes eliminar tu propia cuenta', 'error')
            return redirect(url_for('users.listar_usuarios'))
        
        usuario = Usuario.obtener_por_id(id)
        if usuario and usuario.rol == 'admin':
            from utils.database import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM usuarios WHERE rol = 'admin'")
            count_admins = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            
            if count_admins <= 1:
                flash('No se puede eliminar el último administrador', 'error')
                return redirect(url_for('users.listar_usuarios'))
        
        Usuario.eliminar(id)
        flash('Usuario eliminado exitosamente', 'success')
    except ValueError as e:
        flash(str(e), 'error')
    except Exception as e:
        flash(f'Error al eliminar usuario: {str(e)}', 'error')
    
    return redirect(url_for('users.listar_usuarios'))

@users_bp.route('/inventario')
@login_required
@twofa_required
def inventario():
    """Página principal del inventario"""
    return render_template('inventario.html', user_rol=session.get('user_rol', 'lector'))

@users_bp.route('/perfil')
@login_required
@twofa_required
def perfil_usuario():
    try:
        ultima_ubicacion = Usuario.obtener_ultima_ubicacion(session['user_id'])
        
        return render_template('perfil.html', 
                             usuario=Usuario.obtener_por_id(session['user_id']),
                             ubicacion=ultima_ubicacion,
                             user_rol=session.get('user_rol', 'lector'))
    except Exception as e:
        flash(f'Error al cargar perfil: {str(e)}', 'error')
        return redirect(url_for('users.listar_usuarios'))