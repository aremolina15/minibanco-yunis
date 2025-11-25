from .database import engine, SessionLocal
from .models import Base, Usuario, Cliente, Cuenta, Transaccion
from .services import AuthService
import bcrypt

def init_database():
    # Crear todas las tablas
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Verificar si ya existe un admin
        admin = db.execute(
            "SELECT * FROM usuarios WHERE username = 'admin'"
        ).first()
        
        if not admin:
            # Crear usuario admin por defecto
            from .models import Usuario
            admin_user = Usuario(
                username='admin',
                tipo='admin',
                nombres='Administrador del Sistema',
                email='admin@minibanco.com'
            )
            admin_user.set_password('admin123')
            db.add(admin_user)
            db.commit()
            print("✅ Usuario admin creado: admin / admin123")
        
        # Verificar si hay clientes de prueba
        cliente_test = db.execute(
            "SELECT * FROM usuarios WHERE username = 'cliente_test'"
        ).first()
        
        if not cliente_test:
            # Crear cliente de prueba
            cliente_user = Usuario(
                username='cliente_test',
                tipo='cliente',
                identificacion='123456789',
                nombres='Cliente de Prueba',
                email='cliente@test.com'
            )
            cliente_user.set_password('cliente123')
            db.add(cliente_user)
            db.commit()
            
            # Crear el cliente asociado
            from .models import Cliente
            cliente = Cliente(
                usuario_id=cliente_user.id,
                identificacion='123456789',
                tipo_identificacion='CC',
                nombres='Cliente de Prueba',
                email='cliente@test.com',
                telefono='3001234567'
            )
            db.add(cliente)
            db.commit()
            
            # Crear una cuenta de prueba
            from .models import Cuenta
            cuenta = Cuenta(
                cliente_id=cliente.id,
                numero_cuenta='1000000001',
                tipo_cuenta='AHORROS',
                saldo=1000000.00
            )
            db.add(cuenta)
            db.commit()
            print("✅ Cliente de prueba creado: cliente_test / cliente123")
            
    except Exception as e:
        print(f"❌ Error inicializando base de datos: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_database()