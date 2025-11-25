from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from decimal import Decimal

# Schemas de Autenticación
class LoginRequest(BaseModel):
    username: str
    password: str

class UsuarioBase(BaseModel):
    username: str
    tipo: str
    identificacion: Optional[str] = None
    nombres: Optional[str] = None
    email: Optional[str] = None

class UsuarioResponse(UsuarioBase):
    id: int
    activo: bool
    fecha_registro: datetime
    
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    usuario: UsuarioResponse

# Schemas para Clientes
class ClienteBase(BaseModel):
    identificacion: str
    tipo_identificacion: str = "CC"
    nombres: str
    email: str
    telefono: str

class ClienteCreate(BaseModel):
    identificacion: str
    tipo_identificacion: str = "CC"
    nombres: str
    email: str
    telefono: str
    username: str
    password: str
    
    class Config:
        from_attributes = True

class ClienteResponse(ClienteBase):
    id: int
    usuario_id: int
    fecha_registro: datetime
    username: Optional[str] = None  # Hacer opcional para evitar errores
    
    class Config:
        from_attributes = True

# Schemas para Cuentas
class CuentaBase(BaseModel):
    cliente_id: int
    tipo_cuenta: str

class CuentaCreate(CuentaBase):
    saldo_inicial: Decimal = 0

class CuentaResponse(CuentaBase):
    id: int
    numero_cuenta: str
    saldo: Decimal
    fecha_apertura: datetime
    activa: bool
    cliente_nombre: str = ""
    
    class Config:
        from_attributes = True

# Schemas para Transacciones
class TransaccionBase(BaseModel):
    cuenta_id: int
    tipo: str
    monto: Optional[Decimal] = None
    descripcion: Optional[str] = None

class TransaccionResponse(TransaccionBase):
    id: int
    fecha_transaccion: datetime
    saldo_anterior: Decimal
    saldo_posterior: Decimal
    cuenta_numero: str = ""
    
    class Config:
        from_attributes = True

# Schemas para operaciones
class ConsignacionRequest(BaseModel):
    cuenta_id: int
    monto: Decimal
    descripcion: Optional[str] = ""

class RetiroRequest(BaseModel):
    cuenta_id: int
    monto: Decimal
    descripcion: Optional[str] = ""

class SaldoResponse(BaseModel):
    cuenta_id: int
    saldo: Decimal
    numero_cuenta: str

# ... (schemas existentes)

class CuentaCreateCliente(BaseModel):
    tipo_cuenta: str
    saldo_inicial: Decimal = 0

class TransferenciaRequest(BaseModel):
    cuenta_origen_id: int
    cuenta_destino_id: int
    monto: Decimal
    descripcion: Optional[str] = "Transferencia entre cuentas"