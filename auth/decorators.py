from functools import wraps
from flask import flash, redirect, url_for, session

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor inicia sesión para acceder a esta página', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def twofa_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        if not session.get('twofa_verified', False):
            return redirect(url_for('auth.verificar_2fa'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor inicia sesión para acceder a esta página', 'error')
            return redirect(url_for('auth.login'))
        if session.get('user_rol') != 'admin':
            flash('No tienes permisos de administrador para acceder a esta función', 'error')
            return redirect(url_for('users.listar_usuarios'))
        return f(*args, **kwargs)
    return decorated_function

def editor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor inicia sesión para acceder a esta página', 'error')
            return redirect(url_for('auth.login'))
        if session.get('user_rol') not in ['admin', 'editor']:
            flash('No tienes permisos suficientes para acceder a esta función', 'error')
            return redirect(url_for('users.listar_usuarios'))
        return f(*args, **kwargs)
    return decorated_function