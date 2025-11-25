from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import models, schemas, services
from .database import engine, get_db
import os

# Crear directorio de base de datos si no existe
os.makedirs(os.path.dirname("../../shared_db/"), exist_ok=True)

# Crear la aplicación FastAPI primero
app = FastAPI(
    title="Minibanco API",
    description="API para sistema bancario con FastAPI y autenticación",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependencia para verificar autenticación
def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación requerido"
        )
    
    try:
        token = authorization.replace("Bearer ", "")
        payload = services.AuthService.verificar_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )
        
        usuario = db.execute(
            f"SELECT * FROM usuarios WHERE username = '{payload['sub']}'"
        ).first()
        
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado"
            )
        
        return usuario
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Error de autenticación"
        )

def get_current_admin(current_user = Depends(get_current_user)):
    if current_user.tipo != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren privilegios de administrador"
        )
    return current_user

# Script de inicialización de base de datos
def init_database():
    # Crear todas las tablas
    models.Base.metadata.create_all(bind=engine)
    
    db = next(get_db())
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

# Evento de startup
@app.on_event("startup")
def startup_event():
    init_database()
    print("✅ Base de datos inicializada correctamente")

@app.get("/")
def read_root():
    return {"message": "Bienvenido a Minibanco API", "version": "2.0.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "minibanco-api"}

# Autenticación
@app.post("/auth/login", response_model=schemas.TokenResponse)
def login(login_data: schemas.LoginRequest, db: Session = Depends(get_db)):
    usuario = services.AuthService.autenticar_usuario(db, login_data.username, login_data.password)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas"
        )
    
    token = services.AuthService.crear_token({
        'username': usuario.username,
        'id': usuario.id,
        'tipo': usuario.tipo
    })
    
    usuario_response = {
        'id': usuario.id,
        'username': usuario.username,
        'tipo': usuario.tipo,
        'identificacion': usuario.identificacion,
        'nombres': usuario.nombres,
        'email': usuario.email,
        'activo': usuario.activo,
        'fecha_registro': usuario.fecha_registro
    }
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "usuario": usuario_response
    }

@app.post("/auth/registro", response_model=schemas.TokenResponse)
def registrar_cliente(cliente: schemas.ClienteCreate, db: Session = Depends(get_db)):
    try:
        # Crear cliente (esto ahora retorna el objeto cliente de SQLAlchemy)
        cliente_creado = services.BancoService.crear_cliente(db, cliente)
        
        # Autenticar automáticamente
        usuario = services.AuthService.autenticar_usuario(db, cliente.username, cliente.password)
        token = services.AuthService.crear_token({
            'username': usuario.username,
            'id': usuario.id,
            'tipo': usuario.tipo
        })
        
        usuario_response = {
            'id': usuario.id,
            'username': usuario.username,
            'tipo': usuario.tipo,
            'identificacion': usuario.identificacion,
            'nombres': usuario.nombres,
            'email': usuario.email,
            'activo': usuario.activo,
            'fecha_registro': usuario.fecha_registro
        }
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "usuario": usuario_response
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Endpoints públicos (sin autenticación)
@app.post("/clientes/", response_model=schemas.ClienteResponse)
def crear_cliente(cliente: schemas.ClienteCreate, db: Session = Depends(get_db)):
    try:
        print(f"📥 Datos recibidos para crear cliente:")
        print(f"  - Identificación: {cliente.identificacion}")
        print(f"  - Nombres: {cliente.nombres}")
        print(f"  - Email: {cliente.email}")
        print(f"  - Teléfono: {cliente.telefono}")
        print(f"  - Username: {cliente.username}")
        print(f"  - Password: {'*' * len(cliente.password) if cliente.password else 'None'}")
        
        cliente_creado = services.BancoService.crear_cliente(db, cliente)
        print("✅ Cliente creado exitosamente")
        return cliente_creado
    except ValueError as e:
        print(f"❌ Error creando cliente: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# Endpoints protegidos
@app.get("/clientes/", response_model=list[schemas.ClienteResponse])
def listar_clientes(
    skip: int = 0, 
    limit: int = 100, 
    current_user = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    clientes = services.BancoService.obtener_clientes(db, skip, limit)
    # Ahora clientes es una lista de diccionarios con la estructura correcta
    return clientes


@app.post("/cuentas/", response_model=schemas.CuentaResponse)
def abrir_cuenta(
    cuenta: schemas.CuentaCreate, 
    current_user = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        return services.BancoService.abrir_cuenta(db, cuenta)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/cuentas/", response_model=list[schemas.CuentaResponse])
def listar_cuentas(
    skip: int = 0, 
    limit: int = 100, 
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cuentas = services.BancoService.obtener_cuentas(db, skip, limit)
    result = []
    for cuenta in cuentas:
        cuenta_dict = dict(cuenta)
        result.append(cuenta_dict)
    return result

# Endpoints para clientes
@app.get("/mis-cuentas/", response_model=list[schemas.CuentaResponse])
def listar_mis_cuentas(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Obtener el cliente asociado al usuario
    cliente = db.execute(
        f"SELECT * FROM clientes WHERE usuario_id = {current_user.id}"
    ).first()
    
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    cuentas = services.BancoService.obtener_cuentas_cliente(db, cliente.id)
    
    # Agregar el nombre del cliente a cada cuenta
    for cuenta in cuentas:
        cuenta['cliente_nombre'] = cliente.nombres
    
    return cuentas

# Transacciones
@app.post("/transacciones/consignar/")
def consignar(
    consignacion: schemas.ConsignacionRequest, 
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        cuenta = services.BancoService.realizar_consignacion(db, consignacion)
        return {
            "mensaje": "Consignación exitosa",
            "nuevo_saldo": float(cuenta.saldo),
            "numero_cuenta": cuenta.numero_cuenta
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/transacciones/retirar/")
def retirar(
    retiro: schemas.RetiroRequest, 
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        cuenta = services.BancoService.realizar_retiro(db, retiro)
        return {
            "mensaje": "Retiro exitoso",
            "nuevo_saldo": float(cuenta.saldo),
            "numero_cuenta": cuenta.numero_cuenta
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/cuentas/{cuenta_id}/saldo")
def consultar_saldo(
    cuenta_id: int, 
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        cuenta = services.BancoService.consultar_saldo(db, cuenta_id)
        return {
            "cuenta_id": cuenta_id,
            "saldo": float(cuenta.saldo),
            "numero_cuenta": cuenta.numero_cuenta
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/cuentas/{cuenta_id}/historial")
def obtener_historial(
    cuenta_id: int, 
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        transacciones = services.BancoService.obtener_historial(db, cuenta_id)
        result = []
        for trans in transacciones:
            trans_dict = dict(trans)
            trans_dict['cuenta_numero'] = trans.numero_cuenta
            result.append(trans_dict)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/mis-cuentas/abrir", response_model=schemas.CuentaResponse)
def abrir_mi_cuenta(
    cuenta_data: schemas.CuentaCreateCliente,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Verificar que el usuario sea cliente
        if current_user.tipo != 'cliente':
            raise HTTPException(status_code=403, detail="Solo los clientes pueden abrir cuentas")
        
        # Obtener el cliente asociado al usuario
        cliente = services.BancoService.obtener_cliente_por_usuario(db, current_user.id)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
        # Crear la cuenta para el cliente
        cuenta_creada = services.BancoService.abrir_cuenta_cliente(
            db, 
            cliente.id, 
            cuenta_data.tipo_cuenta, 
            cuenta_data.saldo_inicial
        )
        return cuenta_creada
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Endpoint para transferencias entre cuentas
@app.post("/transacciones/transferir/")
def transferir_entre_cuentas(
    transferencia: schemas.TransferenciaRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        resultado = services.BancoService.realizar_transferencia(db, transferencia, current_user.id)
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Endpoint para obtener todas las cuentas del usuario (propias)
@app.get("/mis-cuentas/todas", response_model=list[schemas.CuentaResponse])
def listar_todas_mis_cuentas(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verificar que el usuario sea cliente
    if current_user.tipo != 'cliente':
        raise HTTPException(status_code=403, detail="Solo los clientes pueden ver sus cuentas")
    
    # Obtener el cliente asociado al usuario
    cliente = services.BancoService.obtener_cliente_por_usuario(db, current_user.id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    # Obtener las cuentas del cliente
    cuentas = services.BancoService.obtener_cuentas_por_cliente(db, cliente.id)
    return cuentas

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)