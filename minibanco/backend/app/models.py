from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
import bcrypt

class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    password_hash = Column(String(255))
    tipo = Column(String(20))  # 'admin' o 'cliente'
    identificacion = Column(String(20), unique=True, index=True, nullable=True)
    nombres = Column(String(100), nullable=True)
    email = Column(String(100), nullable=True)
    telefono = Column(String(15), nullable=True)
    fecha_registro = Column(DateTime(timezone=True), server_default=func.now())
    activo = Column(Boolean, default=True)
    
    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

class Cliente(Base):
    __tablename__ = "clientes"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    identificacion = Column(String(20), unique=True, index=True)
    tipo_identificacion = Column(String(2), default="CC")
    nombres = Column(String(100))
    email = Column(String(100))
    telefono = Column(String(15))
    fecha_registro = Column(DateTime(timezone=True), server_default=func.now())
    
    usuario = relationship("Usuario")

class Cuenta(Base):
    __tablename__ = "cuentas"
    
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    numero_cuenta = Column(String(20), unique=True, index=True)
    tipo_cuenta = Column(String(10))  # AHORROS, CORRIENTE, CDT
    saldo = Column(DECIMAL(15, 2), default=0)
    fecha_apertura = Column(DateTime(timezone=True), server_default=func.now())
    activa = Column(Boolean, default=True)
    
    cliente = relationship("Cliente")

class Transaccion(Base):
    __tablename__ = "transacciones"
    
    id = Column(Integer, primary_key=True, index=True)
    cuenta_id = Column(Integer, ForeignKey("cuentas.id"))
    tipo = Column(String(12))  # CONSIGNACION, RETIRO, CONSULTA
    monto = Column(DECIMAL(15, 2), nullable=True)
    descripcion = Column(Text)
    fecha_transaccion = Column(DateTime(timezone=True), server_default=func.now())
    saldo_anterior = Column(DECIMAL(15, 2))
    saldo_posterior = Column(DECIMAL(15, 2))
    
    cuenta = relationship("Cuenta")