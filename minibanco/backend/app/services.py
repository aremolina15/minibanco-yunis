from decimal import Decimal
from sqlalchemy.orm import Session
from . import models, schemas
import bcrypt
import jwt
from datetime import datetime, timedelta

SECRET_KEY = "minibanco-secret-key-2024"
ALGORITHM = "HS256"

class AuthService:
    """Servicio para autenticación y usuarios"""
    
    @staticmethod
    def crear_usuario(db: Session, usuario_data: dict, tipo: str = "cliente"):
        # Verificar si ya existe el username
        existing = db.execute(
            f"SELECT * FROM usuarios WHERE username = '{usuario_data['username']}'"
        ).first()
        if existing:
            raise ValueError("El nombre de usuario ya existe")
        
        # Crear usuario
        usuario = models.Usuario(
            username=usuario_data['username'],
            tipo=tipo,
            identificacion=usuario_data.get('identificacion'),
            nombres=usuario_data.get('nombres'),
            email=usuario_data.get('email')
        )
        usuario.set_password(usuario_data['password'])
        
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
        return usuario
    
    @staticmethod
    def autenticar_usuario(db: Session, username: str, password: str):
        usuario = db.execute(
            f"SELECT * FROM usuarios WHERE username = '{username}' AND activo = 1"
        ).first()
        
        if not usuario:
            return None
        
        # Crear objeto Usuario temporal para verificar contraseña
        usuario_obj = models.Usuario(
            id=usuario.id,
            username=usuario.username,
            password_hash=usuario.password_hash,
            tipo=usuario.tipo,
            identificacion=usuario.identificacion,
            nombres=usuario.nombres,
            email=usuario.email,
            activo=usuario.activo
        )
        
        if usuario_obj.check_password(password):
            return usuario
        return None
    
    @staticmethod
    def crear_token(usuario_data: dict):
        expire = datetime.utcnow() + timedelta(hours=24)
        to_encode = {
            "sub": usuario_data['username'],
            "id": usuario_data['id'],
            "tipo": usuario_data['tipo'],
            "exp": expire
        }
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verificar_token(token: str):
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.PyJWTError:
            return None

class BancoService:
    """Servicio de negocio para operaciones bancarias"""
    
    @staticmethod
    def crear_cliente(db: Session, cliente_data: schemas.ClienteCreate):
        # Verificar si ya existe la identificación
        existing_cliente = db.execute(
            f"SELECT * FROM clientes WHERE identificacion = '{cliente_data.identificacion}'"
        ).first()
        if existing_cliente:
            raise ValueError("Cliente ya existe con esta identificación")
        
        # Verificar si ya existe el username
        existing_usuario = db.execute(
            f"SELECT * FROM usuarios WHERE username = '{cliente_data.username}'"
        ).first()
        if existing_usuario:
            raise ValueError("El nombre de usuario ya existe")
        
        # Crear usuario primero
        usuario_data = {
            'username': cliente_data.username,
            'password': cliente_data.password,
            'identificacion': cliente_data.identificacion,
            'nombres': cliente_data.nombres,
            'email': cliente_data.email
        }
        
        usuario = AuthService.crear_usuario(db, usuario_data, "cliente")
        
        # Crear cliente
        db_cliente = models.Cliente(
            usuario_id=usuario.id,
            identificacion=cliente_data.identificacion,
            tipo_identificacion=cliente_data.tipo_identificacion,
            nombres=cliente_data.nombres,
            email=cliente_data.email,
            telefono=cliente_data.telefono
        )
        db.add(db_cliente)
        db.commit()
        db.refresh(db_cliente)
        
        # Crear un diccionario con todos los campos necesarios para la respuesta
        cliente_response = {
            'id': db_cliente.id,
            'usuario_id': db_cliente.usuario_id,
            'identificacion': db_cliente.identificacion,
            'tipo_identificacion': db_cliente.tipo_identificacion,
            'nombres': db_cliente.nombres,
            'email': db_cliente.email,
            'telefono': db_cliente.telefono,
            'fecha_registro': db_cliente.fecha_registro,
            'username': cliente_data.username  # Incluir el username
        }
        
        return cliente_response

    @staticmethod
    def obtener_clientes(db: Session, skip: int = 0, limit: int = 100):
        # Usar SQLAlchemy ORM en lugar de ejecutar SQL directo
        from sqlalchemy import select
        stmt = select(models.Cliente, models.Usuario.username).join(
            models.Usuario, models.Cliente.usuario_id == models.Usuario.id
        ).offset(skip).limit(limit)
        
        resultados = db.execute(stmt).all()
        
        # Crear una lista de clientes con username
        clientes_con_username = []
        for cliente, username in resultados:
            # Crear un objeto similar al modelo pero con username
            cliente_data = {
                'id': cliente.id,
                'usuario_id': cliente.usuario_id,
                'identificacion': cliente.identificacion,
                'tipo_identificacion': cliente.tipo_identificacion,
                'nombres': cliente.nombres,
                'email': cliente.email,
                'telefono': cliente.telefono,
                'fecha_registro': cliente.fecha_registro,
                'username': username
            }
            clientes_con_username.append(cliente_data)
            
        return clientes_con_username
    
    @staticmethod
    def abrir_cuenta(db: Session, cuenta: schemas.CuentaCreate):
        # Verificar cliente
        cliente = db.execute(
            f"SELECT * FROM clientes WHERE id = {cuenta.cliente_id}"
        ).first()
        if not cliente:
            raise ValueError("Cliente no encontrado")
        
        # Generar número de cuenta único
        import random
        import string
        numero_cuenta = ''.join(random.choices(string.digits, k=10))
        
        # Verificar que no exista
        while db.execute(f"SELECT * FROM cuentas WHERE numero_cuenta = '{numero_cuenta}'").first():
            numero_cuenta = ''.join(random.choices(string.digits, k=10))
        
        db_cuenta = models.Cuenta(
            cliente_id=cuenta.cliente_id,
            numero_cuenta=numero_cuenta,
            tipo_cuenta=cuenta.tipo_cuenta,
            saldo=cuenta.saldo_inicial
        )
        db.add(db_cuenta)
        db.commit()
        db.refresh(db_cuenta)
        
        # Registrar transacción inicial si hay saldo
        if cuenta.saldo_inicial > 0:
            transaccion = models.Transaccion(
                cuenta_id=db_cuenta.id,
                tipo="CONSIGNACION",
                monto=cuenta.saldo_inicial,
                descripcion="Apertura de cuenta",
                saldo_anterior=0,
                saldo_posterior=cuenta.saldo_inicial
            )
            db.add(transaccion)
            db.commit()
        
        return db_cuenta
    
    @staticmethod
    def realizar_consignacion(db: Session, consignacion: schemas.ConsignacionRequest):
        # Usar SQLAlchemy ORM para obtener la cuenta
        from sqlalchemy import select
        stmt = select(models.Cuenta).where(models.Cuenta.id == consignacion.cuenta_id)
        cuenta = db.execute(stmt).scalar_one_or_none()
        
        if not cuenta:
            raise ValueError("Cuenta no encontrada")
        if not cuenta.activa:
            raise ValueError("Cuenta inactiva")
        
        saldo_anterior = cuenta.saldo
        nuevo_saldo = saldo_anterior + consignacion.monto
        
        # Actualizar saldo usando ORM
        cuenta.saldo = nuevo_saldo
        db.commit()
        db.refresh(cuenta)
        
        transaccion = models.Transaccion(
            cuenta_id=consignacion.cuenta_id,
            tipo="CONSIGNACION",
            monto=consignacion.monto,
            descripcion=consignacion.descripcion or "Consignación",
            saldo_anterior=saldo_anterior,
            saldo_posterior=nuevo_saldo
        )
        
        db.add(transaccion)
        db.commit()
        
        return cuenta
    
    @staticmethod
    def realizar_retiro(db: Session, retiro: schemas.RetiroRequest):
        # Usar SQLAlchemy ORM para obtener la cuenta
        from sqlalchemy import select
        stmt = select(models.Cuenta).where(models.Cuenta.id == retiro.cuenta_id)
        cuenta = db.execute(stmt).scalar_one_or_none()
        
        if not cuenta:
            raise ValueError("Cuenta no encontrada")
        if not cuenta.activa:
            raise ValueError("Cuenta inactiva")
        if cuenta.saldo < retiro.monto:
            raise ValueError("Saldo insuficiente")
        
        saldo_anterior = cuenta.saldo
        nuevo_saldo = saldo_anterior - retiro.monto
        
        # Actualizar saldo usando ORM
        cuenta.saldo = nuevo_saldo
        db.commit()
        db.refresh(cuenta)
        
        transaccion = models.Transaccion(
            cuenta_id=retiro.cuenta_id,
            tipo="RETIRO",
            monto=retiro.monto,
            descripcion=retiro.descripcion or "Retiro",
            saldo_anterior=saldo_anterior,
            saldo_posterior=nuevo_saldo
        )
        
        db.add(transaccion)
        db.commit()
        
        return cuenta
    
    @staticmethod
    def consultar_saldo(db: Session, cuenta_id: int):
        # Usar SQLAlchemy ORM para obtener la cuenta
        from sqlalchemy import select
        stmt = select(models.Cuenta).where(models.Cuenta.id == cuenta_id)
        cuenta = db.execute(stmt).scalar_one_or_none()
        
        if not cuenta:
            raise ValueError("Cuenta no encontrada")
        if not cuenta.activa:
            raise ValueError("Cuenta inactiva")
        
        # Registrar consulta
        transaccion = models.Transaccion(
            cuenta_id=cuenta_id,
            tipo="CONSULTA",
            monto=None,
            descripcion="Consulta de saldo",
            saldo_anterior=cuenta.saldo,
            saldo_posterior=cuenta.saldo
        )
        db.add(transaccion)
        db.commit()
        
        return cuenta
    
    @staticmethod
    def obtener_historial(db: Session, cuenta_id: int):
        from sqlalchemy import select
        stmt = select(
            models.Transaccion, 
            models.Cuenta.numero_cuenta
        ).join(
            models.Cuenta, 
            models.Transaccion.cuenta_id == models.Cuenta.id
        ).where(
            models.Transaccion.cuenta_id == cuenta_id
        ).order_by(models.Transaccion.fecha_transaccion.desc())
        
        resultados = db.execute(stmt).all()
        
        historial = []
        for transaccion, numero_cuenta in resultados:
            trans_dict = {
                'id': transaccion.id,
                'cuenta_id': transaccion.cuenta_id,
                'tipo': transaccion.tipo,
                'monto': transaccion.monto,
                'descripcion': transaccion.descripcion,
                'fecha_transaccion': transaccion.fecha_transaccion,
                'saldo_anterior': transaccion.saldo_anterior,
                'saldo_posterior': transaccion.saldo_posterior,
                'cuenta_numero': numero_cuenta
            }
            historial.append(trans_dict)
            
        return historial
    
    @staticmethod
    def obtener_cuentas(db: Session, skip: int = 0, limit: int = 100):
        from sqlalchemy import select
        stmt = select(
            models.Cuenta,
            models.Cliente.nombres.label('cliente_nombre')
        ).join(
            models.Cliente,
            models.Cuenta.cliente_id == models.Cliente.id
        ).offset(skip).limit(limit)
        
        resultados = db.execute(stmt).all()
        
        cuentas = []
        for cuenta, cliente_nombre in resultados:
            cuenta_dict = {
                'id': cuenta.id,
                'cliente_id': cuenta.cliente_id,
                'numero_cuenta': cuenta.numero_cuenta,
                'tipo_cuenta': cuenta.tipo_cuenta,
                'saldo': cuenta.saldo,
                'fecha_apertura': cuenta.fecha_apertura,
                'activa': cuenta.activa,
                'cliente_nombre': cliente_nombre
            }
            cuentas.append(cuenta_dict)
            
        return cuentas
    
    @staticmethod
    def obtener_cuentas_cliente(db: Session, usuario_id: int):
        """Obtiene las cuentas de un cliente específico"""
        # Primero obtener el cliente por usuario_id
        cliente = BancoService.obtener_cliente_por_usuario(db, usuario_id)
        if not cliente:
            return []
        
        # Luego obtener las cuentas del cliente
        from sqlalchemy import select
        stmt = select(
            models.Cuenta,
            models.Cliente.nombres.label('cliente_nombre')
        ).join(
            models.Cliente,
            models.Cuenta.cliente_id == models.Cliente.id
        ).where(
            models.Cuenta.cliente_id == cliente.id,
            models.Cuenta.activa == True
        )
        
        resultados = db.execute(stmt).all()
        
        cuentas = []
        for cuenta, cliente_nombre in resultados:
            cuenta_dict = {
                'id': cuenta.id,
                'cliente_id': cuenta.cliente_id,
                'numero_cuenta': cuenta.numero_cuenta,
                'tipo_cuenta': cuenta.tipo_cuenta,
                'saldo': cuenta.saldo,
                'fecha_apertura': cuenta.fecha_apertura,
                'activa': cuenta.activa,
                'cliente_nombre': cliente_nombre
            }
            cuentas.append(cuenta_dict)
            
        return cuentas
    
    
    @staticmethod
    def abrir_cuenta_cliente(db: Session, cliente_id: int, tipo_cuenta: str, saldo_inicial: Decimal = 0):
        """Abrir cuenta para un cliente específico"""
        # Validar tipo de cuenta
        tipos_validos = ['AHORROS', 'CORRIENTE', 'CDT']
        if tipo_cuenta not in tipos_validos:
            raise ValueError(f"Tipo de cuenta no válido. Debe ser: {', '.join(tipos_validos)}")
        
        # Validar saldo inicial
        if saldo_inicial < 0:
            raise ValueError("El saldo inicial no puede ser negativo")
        
        # Generar número de cuenta único
        import random
        import string
        numero_cuenta = ''.join(random.choices(string.digits, k=10))
        
        # Verificar que no exista
        while db.execute(f"SELECT * FROM cuentas WHERE numero_cuenta = '{numero_cuenta}'").first():
            numero_cuenta = ''.join(random.choices(string.digits, k=10))
        
        # Crear cuenta
        db_cuenta = models.Cuenta(
            cliente_id=cliente_id,
            numero_cuenta=numero_cuenta,
            tipo_cuenta=tipo_cuenta,
            saldo=saldo_inicial
        )
        db.add(db_cuenta)
        db.commit()
        db.refresh(db_cuenta)
        
        # Registrar transacción inicial si hay saldo
        if saldo_inicial > 0:
            transaccion = models.Transaccion(
                cuenta_id=db_cuenta.id,
                tipo="CONSIGNACION",
                monto=saldo_inicial,
                descripcion="Apertura de cuenta",
                saldo_anterior=0,
                saldo_posterior=saldo_inicial
            )
            db.add(transaccion)
            db.commit()
        
        return db_cuenta

    @staticmethod
    def realizar_transferencia(db: Session, transferencia: schemas.TransferenciaRequest, usuario_id: int):
        """Realizar transferencia entre cuentas del mismo usuario"""
        # Verificar que las cuentas pertenezcan al mismo cliente
        from sqlalchemy import select
        
        # Obtener información del cliente
        cliente = BancoService.obtener_cliente_por_usuario(db, usuario_id)
        if not cliente:
            raise ValueError("Cliente no encontrado")
        
        # Verificar que la cuenta origen pertenezca al cliente
        stmt_origen = select(models.Cuenta).where(
            models.Cuenta.id == transferencia.cuenta_origen_id,
            models.Cuenta.cliente_id == cliente.id
        )
        cuenta_origen = db.execute(stmt_origen).scalar_one_or_none()
        
        if not cuenta_origen:
            raise ValueError("La cuenta origen no existe o no te pertenece")
        
        # Verificar que la cuenta destino exista
        stmt_destino = select(models.Cuenta).where(
            models.Cuenta.id == transferencia.cuenta_destino_id
        )
        cuenta_destino = db.execute(stmt_destino).scalar_one_or_none()
        
        if not cuenta_destino:
            raise ValueError("La cuenta destino no existe")
        
        # Verificar que la cuenta origen tenga saldo suficiente
        if cuenta_origen.saldo < transferencia.monto:
            raise ValueError("Saldo insuficiente en la cuenta origen")
        
        # Verificar que las cuentas estén activas
        if not cuenta_origen.activa:
            raise ValueError("La cuenta origen está inactiva")
        if not cuenta_destino.activa:
            raise ValueError("La cuenta destino está inactiva")
        
        # Realizar la transferencia (retiro + consignación)
        saldo_anterior_origen = cuenta_origen.saldo
        saldo_anterior_destino = cuenta_destino.saldo
        
        # Actualizar saldos
        cuenta_origen.saldo -= transferencia.monto
        cuenta_destino.saldo += transferencia.monto
        
        # Registrar transacciones
        transaccion_retiro = models.Transaccion(
            cuenta_id=transferencia.cuenta_origen_id,
            tipo="RETIRO",
            monto=transferencia.monto,
            descripcion=f"Transferencia a cuenta {cuenta_destino.numero_cuenta} - {transferencia.descripcion}",
            saldo_anterior=saldo_anterior_origen,
            saldo_posterior=cuenta_origen.saldo
        )
        
        transaccion_consignacion = models.Transaccion(
            cuenta_id=transferencia.cuenta_destino_id,
            tipo="CONSIGNACION",
            monto=transferencia.monto,
            descripcion=f"Transferencia de cuenta {cuenta_origen.numero_cuenta} - {transferencia.descripcion}",
            saldo_anterior=saldo_anterior_destino,
            saldo_posterior=cuenta_destino.saldo
        )
        
        db.add(transaccion_retiro)
        db.add(transaccion_consignacion)
        db.commit()
        
        return {
            "mensaje": "Transferencia exitosa",
            "cuenta_origen": cuenta_origen.numero_cuenta,
            "cuenta_destino": cuenta_destino.numero_cuenta,
            "monto": float(transferencia.monto),
            "nuevo_saldo_origen": float(cuenta_origen.saldo),
            "nuevo_saldo_destino": float(cuenta_destino.saldo)
        }
    
    @staticmethod
    def obtener_cliente_por_usuario(db: Session, usuario_id: int):
        """Obtiene el cliente asociado a un usuario"""
        from sqlalchemy import select
        stmt = select(models.Cliente).where(models.Cliente.usuario_id == usuario_id)
        resultado = db.execute(stmt).first()
        return resultado[0] if resultado else None

    @staticmethod
    def obtener_cuentas_por_cliente(db: Session, cliente_id: int):
        """Obtiene todas las cuentas de un cliente específico"""
        from sqlalchemy import select
        
        stmt = select(
            models.Cuenta,
            models.Cliente.nombres.label('cliente_nombre')
        ).join(
            models.Cliente,
            models.Cuenta.cliente_id == models.Cliente.id
        ).where(
            models.Cuenta.cliente_id == cliente_id
        )
        
        resultados = db.execute(stmt).all()
        
        cuentas = []
        for cuenta, cliente_nombre in resultados:
            cuenta_dict = {
                'id': cuenta.id,
                'cliente_id': cuenta.cliente_id,
                'numero_cuenta': cuenta.numero_cuenta,
                'tipo_cuenta': cuenta.tipo_cuenta,
                'saldo': float(cuenta.saldo) if cuenta.saldo else 0.0,
                'fecha_apertura': cuenta.fecha_apertura,
                'activa': cuenta.activa,
                'cliente_nombre': cliente_nombre
            }
            cuentas.append(cuenta_dict)
            
        return cuentas

    @staticmethod
    def obtener_cuentas_usuario_actual(db: Session, usuario_id: int):
        """Obtiene todas las cuentas del usuario actual en una sola consulta"""
        from sqlalchemy import select
        
        stmt = select(
            models.Cuenta,
            models.Cliente.nombres.label('cliente_nombre')
        ).join(
            models.Cliente,
            models.Cuenta.cliente_id == models.Cliente.id
        ).join(
            models.Usuario,
            models.Cliente.usuario_id == models.Usuario.id
        ).where(
            models.Usuario.id == usuario_id
        )
        
        resultados = db.execute(stmt).all()
        
        cuentas = []
        for cuenta, cliente_nombre in resultados:
            cuenta_dict = {
                'id': cuenta.id,
                'cliente_id': cuenta.cliente_id,
                'numero_cuenta': cuenta.numero_cuenta,
                'tipo_cuenta': cuenta.tipo_cuenta,
                'saldo': float(cuenta.saldo) if cuenta.saldo else 0.0,
                'fecha_apertura': cuenta.fecha_apertura,
                'activa': cuenta.activa,
                'cliente_nombre': cliente_nombre
            }
            cuentas.append(cuenta_dict)
            
        return cuentas

    # =================== CRUD USUARIOS ===================
    @staticmethod
    def obtener_usuarios(db: Session, skip: int = 0, limit: int = 100):
        """Obtener todos los usuarios (solo admin)"""
        from sqlalchemy import select
        stmt = select(models.Usuario).offset(skip).limit(limit)
        usuarios = db.execute(stmt).scalars().all()
        return usuarios
    
    @staticmethod
    def obtener_usuario_por_id(db: Session, usuario_id: int):
        """Obtener un usuario por ID"""
        from sqlalchemy import select
        stmt = select(models.Usuario).where(models.Usuario.id == usuario_id)
        usuario = db.execute(stmt).scalar_one_or_none()
        if not usuario:
            raise ValueError("Usuario no encontrado")
        return usuario
    
    @staticmethod
    def actualizar_usuario(db: Session, usuario_id: int, usuario_update: dict):
        """Actualizar un usuario"""
        from sqlalchemy import select
        stmt = select(models.Usuario).where(models.Usuario.id == usuario_id)
        usuario = db.execute(stmt).scalar_one_or_none()
        
        if not usuario:
            raise ValueError("Usuario no encontrado")
        
        # Actualizar campos
        if usuario_update.get('nombres'):
            usuario.nombres = usuario_update['nombres']
        if usuario_update.get('email'):
            usuario.email = usuario_update['email']
        if usuario_update.get('telefono'):
            usuario.telefono = usuario_update['telefono']
        if usuario_update.get('activo') is not None:
            usuario.activo = usuario_update['activo']
        if usuario_update.get('password'):
            usuario.set_password(usuario_update['password'])
        
        db.commit()
        db.refresh(usuario)
        return usuario
    
    @staticmethod
    def eliminar_usuario(db: Session, usuario_id: int):
        """Eliminar un usuario permanentemente (incluye cliente, cuentas y transacciones asociadas)"""
        from sqlalchemy import select
        stmt = select(models.Usuario).where(models.Usuario.id == usuario_id)
        usuario = db.execute(stmt).scalar_one_or_none()
        
        if not usuario:
            raise ValueError("Usuario no encontrado")
        
        # No permitir eliminar admin principal
        if usuario.username == 'admin':
            raise ValueError("No se puede eliminar el usuario administrador principal")
        
        # Buscar el cliente asociado
        cliente = db.execute(
            select(models.Cliente).where(models.Cliente.usuario_id == usuario_id)
        ).scalar_one_or_none()
        
        if cliente:
            # Obtener todas las cuentas del cliente
            cuentas = db.execute(
                select(models.Cuenta).where(models.Cuenta.cliente_id == cliente.id)
            ).scalars().all()
            
            # Eliminar transacciones de cada cuenta
            for cuenta in cuentas:
                db.execute(
                    select(models.Transaccion).where(models.Transaccion.cuenta_id == cuenta.id)
                )
                db.query(models.Transaccion).filter(
                    models.Transaccion.cuenta_id == cuenta.id
                ).delete()
            
            # Eliminar todas las cuentas
            db.query(models.Cuenta).filter(models.Cuenta.cliente_id == cliente.id).delete()
            
            # Eliminar el cliente
            db.delete(cliente)
        
        # Eliminar el usuario
        db.delete(usuario)
        db.commit()
        return {"mensaje": "Usuario y todos sus datos eliminados permanentemente"}

    # =================== CRUD CLIENTES ===================
    @staticmethod
    def obtener_cliente_por_id(db: Session, cliente_id: int):
        """Obtener un cliente por ID con información del usuario"""
        from sqlalchemy import select
        stmt = select(
            models.Cliente,
            models.Usuario.username
        ).join(
            models.Usuario,
            models.Cliente.usuario_id == models.Usuario.id
        ).where(
            models.Cliente.id == cliente_id
        )
        
        resultado = db.execute(stmt).first()
        if not resultado:
            raise ValueError("Cliente no encontrado")
        
        cliente, username = resultado
        return {
            'id': cliente.id,
            'usuario_id': cliente.usuario_id,
            'identificacion': cliente.identificacion,
            'tipo_identificacion': cliente.tipo_identificacion,
            'nombres': cliente.nombres,
            'email': cliente.email,
            'telefono': cliente.telefono,
            'fecha_registro': cliente.fecha_registro,
            'username': username
        }
    
    @staticmethod
    def actualizar_cliente(db: Session, cliente_id: int, cliente_update: dict):
        """Actualizar información de un cliente"""
        from sqlalchemy import select
        stmt = select(models.Cliente).where(models.Cliente.id == cliente_id)
        cliente = db.execute(stmt).scalar_one_or_none()
        
        if not cliente:
            raise ValueError("Cliente no encontrado")
        
        # Actualizar campos
        if cliente_update.get('tipo_identificacion'):
            cliente.tipo_identificacion = cliente_update['tipo_identificacion']
        if cliente_update.get('nombres'):
            cliente.nombres = cliente_update['nombres']
        if cliente_update.get('email'):
            cliente.email = cliente_update['email']
        if cliente_update.get('telefono'):
            cliente.telefono = cliente_update['telefono']
        
        db.commit()
        db.refresh(cliente)
        
        # Retornar con username
        usuario = db.execute(
            select(models.Usuario).where(models.Usuario.id == cliente.usuario_id)
        ).scalar_one()
        
        return {
            'id': cliente.id,
            'usuario_id': cliente.usuario_id,
            'identificacion': cliente.identificacion,
            'tipo_identificacion': cliente.tipo_identificacion,
            'nombres': cliente.nombres,
            'email': cliente.email,
            'telefono': cliente.telefono,
            'fecha_registro': cliente.fecha_registro,
            'username': usuario.username
        }
    
    @staticmethod
    def eliminar_cliente(db: Session, cliente_id: int):
        """Eliminar un cliente permanentemente (incluye cuentas, transacciones y usuario asociado)"""
        from sqlalchemy import select
        stmt = select(models.Cliente).where(models.Cliente.id == cliente_id)
        cliente = db.execute(stmt).scalar_one_or_none()
        
        if not cliente:
            raise ValueError("Cliente no encontrado")
        
        # Verificar que el usuario asociado no sea admin
        usuario = db.execute(
            select(models.Usuario).where(models.Usuario.id == cliente.usuario_id)
        ).scalar_one_or_none()
        
        if usuario and usuario.username == 'admin':
            raise ValueError("No se puede eliminar el cliente asociado al administrador")
        
        # Obtener todas las cuentas del cliente
        cuentas = db.execute(
            select(models.Cuenta).where(models.Cuenta.cliente_id == cliente_id)
        ).scalars().all()
        
        # Eliminar transacciones de cada cuenta
        for cuenta in cuentas:
            db.query(models.Transaccion).filter(
                models.Transaccion.cuenta_id == cuenta.id
            ).delete()
        
        # Eliminar todas las cuentas
        db.query(models.Cuenta).filter(models.Cuenta.cliente_id == cliente_id).delete()
        
        # Eliminar el cliente
        db.delete(cliente)
        
        # Eliminar el usuario asociado
        if usuario:
            db.delete(usuario)
        
        db.commit()
        return {"mensaje": "Cliente, usuario y todos sus datos eliminados permanentemente"}

    # =================== CRUD CUENTAS ===================
    @staticmethod
    def obtener_cuenta_por_id(db: Session, cuenta_id: int):
        """Obtener una cuenta por ID con información del cliente"""
        from sqlalchemy import select
        stmt = select(
            models.Cuenta,
            models.Cliente.nombres.label('cliente_nombre')
        ).join(
            models.Cliente,
            models.Cuenta.cliente_id == models.Cliente.id
        ).where(
            models.Cuenta.id == cuenta_id
        )
        
        resultado = db.execute(stmt).first()
        if not resultado:
            raise ValueError("Cuenta no encontrada")
        
        cuenta, cliente_nombre = resultado
        return {
            'id': cuenta.id,
            'cliente_id': cuenta.cliente_id,
            'numero_cuenta': cuenta.numero_cuenta,
            'tipo_cuenta': cuenta.tipo_cuenta,
            'saldo': float(cuenta.saldo),
            'fecha_apertura': cuenta.fecha_apertura,
            'activa': cuenta.activa,
            'cliente_nombre': cliente_nombre
        }
    
    @staticmethod
    def actualizar_cuenta(db: Session, cuenta_id: int, cuenta_update: dict):
        """Actualizar una cuenta"""
        from sqlalchemy import select
        stmt = select(models.Cuenta).where(models.Cuenta.id == cuenta_id)
        cuenta = db.execute(stmt).scalar_one_or_none()
        
        if not cuenta:
            raise ValueError("Cuenta no encontrada")
        
        # Actualizar campos permitidos
        if cuenta_update.get('tipo_cuenta'):
            tipos_validos = ['AHORROS', 'CORRIENTE', 'CDT']
            if cuenta_update['tipo_cuenta'] not in tipos_validos:
                raise ValueError(f"Tipo de cuenta no válido. Debe ser: {', '.join(tipos_validos)}")
            cuenta.tipo_cuenta = cuenta_update['tipo_cuenta']
        
        if cuenta_update.get('activa') is not None:
            cuenta.activa = cuenta_update['activa']
        
        db.commit()
        db.refresh(cuenta)
        
        # Obtener nombre del cliente
        cliente = db.execute(
            select(models.Cliente).where(models.Cliente.id == cuenta.cliente_id)
        ).scalar_one()
        
        return {
            'id': cuenta.id,
            'cliente_id': cuenta.cliente_id,
            'numero_cuenta': cuenta.numero_cuenta,
            'tipo_cuenta': cuenta.tipo_cuenta,
            'saldo': float(cuenta.saldo),
            'fecha_apertura': cuenta.fecha_apertura,
            'activa': cuenta.activa,
            'cliente_nombre': cliente.nombres
        }
    
    @staticmethod
    def eliminar_cuenta(db: Session, cuenta_id: int):
        """Eliminar una cuenta permanentemente (incluye transacciones asociadas)"""
        from sqlalchemy import select
        stmt = select(models.Cuenta).where(models.Cuenta.id == cuenta_id)
        cuenta = db.execute(stmt).scalar_one_or_none()
        
        if not cuenta:
            raise ValueError("Cuenta no encontrada")
        
        # Eliminar todas las transacciones asociadas a la cuenta
        db.query(models.Transaccion).filter(
            models.Transaccion.cuenta_id == cuenta_id
        ).delete()
        
        # Eliminar la cuenta
        db.delete(cuenta)
        db.commit()
        return {"mensaje": "Cuenta y todas sus transacciones eliminadas permanentemente"}

    # =================== CRUD TRANSACCIONES ===================
    @staticmethod
    def obtener_todas_transacciones(db: Session, skip: int = 0, limit: int = 100):
        """Obtener todas las transacciones (solo admin)"""
        from sqlalchemy import select
        stmt = select(
            models.Transaccion,
            models.Cuenta.numero_cuenta,
            models.Cliente.nombres.label('cliente_nombre')
        ).join(
            models.Cuenta,
            models.Transaccion.cuenta_id == models.Cuenta.id
        ).join(
            models.Cliente,
            models.Cuenta.cliente_id == models.Cliente.id
        ).order_by(
            models.Transaccion.fecha_transaccion.desc()
        ).offset(skip).limit(limit)
        
        resultados = db.execute(stmt).all()
        
        transacciones = []
        for transaccion, numero_cuenta, cliente_nombre in resultados:
            trans_dict = {
                'id': transaccion.id,
                'cuenta_id': transaccion.cuenta_id,
                'tipo': transaccion.tipo,
                'monto': float(transaccion.monto) if transaccion.monto else None,
                'descripcion': transaccion.descripcion,
                'fecha_transaccion': transaccion.fecha_transaccion,
                'saldo_anterior': float(transaccion.saldo_anterior),
                'saldo_posterior': float(transaccion.saldo_posterior),
                'cuenta_numero': numero_cuenta,
                'cliente_nombre': cliente_nombre
            }
            transacciones.append(trans_dict)
        
        return transacciones
    
    @staticmethod
    def obtener_transaccion_por_id(db: Session, transaccion_id: int):
        """Obtener una transacción por ID"""
        from sqlalchemy import select
        stmt = select(
            models.Transaccion,
            models.Cuenta.numero_cuenta,
            models.Cliente.nombres.label('cliente_nombre')
        ).join(
            models.Cuenta,
            models.Transaccion.cuenta_id == models.Cuenta.id
        ).join(
            models.Cliente,
            models.Cuenta.cliente_id == models.Cliente.id
        ).where(
            models.Transaccion.id == transaccion_id
        )
        
        resultado = db.execute(stmt).first()
        if not resultado:
            raise ValueError("Transacción no encontrada")
        
        transaccion, numero_cuenta, cliente_nombre = resultado
        return {
            'id': transaccion.id,
            'cuenta_id': transaccion.cuenta_id,
            'tipo': transaccion.tipo,
            'monto': float(transaccion.monto) if transaccion.monto else None,
            'descripcion': transaccion.descripcion,
            'fecha_transaccion': transaccion.fecha_transaccion,
            'saldo_anterior': float(transaccion.saldo_anterior),
            'saldo_posterior': float(transaccion.saldo_posterior),
            'cuenta_numero': numero_cuenta,
            'cliente_nombre': cliente_nombre
        }
    
    @staticmethod
    def actualizar_transaccion(db: Session, transaccion_id: int, transaccion_update: dict):
        """Actualizar descripción de una transacción"""
        from sqlalchemy import select
        stmt = select(models.Transaccion).where(models.Transaccion.id == transaccion_id)
        transaccion = db.execute(stmt).scalar_one_or_none()
        
        if not transaccion:
            raise ValueError("Transacción no encontrada")
        
        # Solo permitir actualizar descripción
        if transaccion_update.get('descripcion'):
            transaccion.descripcion = transaccion_update['descripcion']
        
        db.commit()
        db.refresh(transaccion)
        
        # Obtener información adicional
        cuenta = db.execute(
            select(models.Cuenta).where(models.Cuenta.id == transaccion.cuenta_id)
        ).scalar_one()
        
        cliente = db.execute(
            select(models.Cliente).where(models.Cliente.id == cuenta.cliente_id)
        ).scalar_one()
        
        return {
            'id': transaccion.id,
            'cuenta_id': transaccion.cuenta_id,
            'tipo': transaccion.tipo,
            'monto': float(transaccion.monto) if transaccion.monto else None,
            'descripcion': transaccion.descripcion,
            'fecha_transaccion': transaccion.fecha_transaccion,
            'saldo_anterior': float(transaccion.saldo_anterior),
            'saldo_posterior': float(transaccion.saldo_posterior),
            'cuenta_numero': cuenta.numero_cuenta,
            'cliente_nombre': cliente.nombres
        }
    
    @staticmethod
    def eliminar_transaccion(db: Session, transaccion_id: int):
        """Eliminar una transacción (solo descripción, no afecta saldos)"""
        from sqlalchemy import select
        stmt = select(models.Transaccion).where(models.Transaccion.id == transaccion_id)
        transaccion = db.execute(stmt).scalar_one_or_none()
        
        if not transaccion:
            raise ValueError("Transacción no encontrada")
        
        # NOTA: En un sistema real, no deberías eliminar transacciones
        # porque afectaría la integridad contable. Aquí lo permitimos solo para CRUD completo.
        # En producción, mejor sería marcarla como "anulada" o algo similar.
        db.delete(transaccion)
        db.commit()
        return {"mensaje": "Transacción eliminada exitosamente"}