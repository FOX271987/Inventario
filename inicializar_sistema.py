# inicializar_sistema.py - VERSIÓN SIMPLIFICADA
from app_simple import app

with app.app_context():
    from models import db, Usuario, Producto
    
    print("📦 Inicializando base de datos...")
    db.create_all()
    print("✅ Base de datos creada")
    
    print("\n👥 Creando usuarios...")
    
    # Crear usuarios con try-except individual
    try:
        if not Usuario.query.filter_by(email='admin@test.com').first():
            Usuario.crear('Admin Test', 'admin@test.com', 'admin123', 'admin')
            print("  ✅ admin: admin@test.com")
    except:
        print("  ⏭️  admin@test.com ya existe")
    
    try:
        if not Usuario.query.filter_by(email='editor@test.com').first():
            Usuario.crear('Editor Test', 'editor@test.com', 'editor123', 'editor')
            print("  ✅ editor: editor@test.com")
    except:
        print("  ⏭️  editor@test.com ya existe")
    
    try:
        if not Usuario.query.filter_by(email='lector@test.com').first():
            Usuario.crear('Lector Test', 'lector@test.com', 'lector123', 'lector')
            print("  ✅ lector: lector@test.com")
    except:
        print("  ⏭️  lector@test.com ya existe")
    
    print("\n📦 Creando productos...")
    productos = [
        {'Codigo': 'PROD-001', 'Nombre': 'Laptop Dell', 'Categoria': 'Electrónica', 
         'Unidad': 'pz', 'Stock_Minimo': 5, 'Stock_Actual': 12},
        {'Codigo': 'PROD-002', 'Nombre': 'Mouse Logitech', 'Categoria': 'Accesorios',
         'Unidad': 'pz', 'Stock_Minimo': 10, 'Stock_Actual': 3},
    ]
    
    for p in productos:
        try:
            if not Producto.query.filter_by(Codigo=p['Codigo']).first():
                producto = Producto(**p)
                db.session.add(producto)
                print(f"  ✅ {p['Nombre']}")
        except:
            print(f"  ⏭️  {p['Codigo']} ya existe")
    
    db.session.commit()
    
    print("\n✅ SISTEMA INICIALIZADO")
    print("🌐 Login: http://localhost:5000/productos/login")
    print("🔑 Admin: admin@test.com / admin123")