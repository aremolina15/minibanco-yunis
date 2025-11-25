# 🏦 Minibanco - Sistema de Gestión Bancaria

## 📋 Descripción del Proyecto

Minibanco es una aplicación web completa que implementa un sistema de gestión bancaria, desarrollada con **Django** (frontend) y **FastAPI** (backend), utilizando **SQLite** como base de datos. La aplicación permite el registro de clientes, apertura de cuentas bancarias y realización de operaciones financieras.

## 🎯 Objetivos Cumplidos

### ✅ Requisitos Académicos Implementados

- **Aplicación web** que soluciona una necesidad del entorno (gestión bancaria digital)
- **Patrón de diseño MVC/MTV** claramente implementado
- **Métodos de negocio** específicos del dominio bancario
- **Servicios REST** completos y documentados
- **Integración frontend/backend** mediante consumo de APIs
- **Arquitectura en capas** bien definida

## 🏗️ Arquitectura del Sistema

### Backend (FastAPI)
- **Framework**: FastAPI
- **Puerto**: 8001
- **Base de datos**: SQLite
- **Características**: API REST, documentación automática Swagger, validación con Pydantic

### Frontend (Django)
- **Framework**: Django
- **Puerto**: 8000  
- **Características**: Templates HTML, Bootstrap, consumo de APIs REST

### Base de Datos
- **Motor**: SQLite compartida
- **Tablas**: Clientes, Cuentas, Transacciones
- **Ubicación**: `shared_db/minibanco.db`

## 📊 Funcionalidades Implementadas

### 👥 Gestión de Clientes
- Registro de clientes con identificación única
- Tipos de identificación: Cédula, Pasaporte, Cédula de extranjería
- Información completa: nombres, email, teléfono

### 💳 Gestión de Cuentas
- Apertura de cuentas bancarias
- Tipos de cuenta: Ahorros, Corriente, CDT
- Generación automática de números de cuenta únicos
- Control de estado (activa/inactiva)

### 💰 Operaciones Bancarias
- **Consignaciones**: Agregar fondos a las cuentas
- **Retiros**: Retirar dinero (con validación de saldo)
- **Consultas de saldo**: Ver saldo actual
- **Historial de transacciones**: Auditoría completa

## 🛠️ Tecnologías Utilizadas

### Backend
```python
FastAPI==0.104.1
SQLAlchemy==1.4.46
Pydantic==2.5.0
Uvicorn==0.24.0
```

### Frontend
```python
Django==4.2.7
Requests==2.31.0
Bootstrap==5.1.3
```

## 🚀 Instalación y Configuración

### Prerrequisitos
- Python 3.8+
- pip (gestor de paquetes de Python)

### 1. Clonar o Crear la Estructura del Proyecto
```bash
# Crear estructura de directorios
mkdir -p minibanco/{backend/app,frontend/banco/templates/banco,shared_db}
cd minibanco
```

### 2. Crear Entorno Virtual
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows
```

### 3. Instalar Dependencias
```bash
# Backend
cd backend
pip install fastapi==0.104.1 uvicorn==0.24.0 sqlalchemy==1.4.46 pydantic==2.5.0

# Frontend  
cd ../frontend
pip install Django==4.2.7 requests==2.31.0
```

### 4. Configurar Archivos
Copiar todos los archivos proporcionados en sus respectivos directorios:
- `backend/app/` - Código del backend FastAPI
- `frontend/` - Código del frontend Django
- `frontend/banco/templates/banco/` - Templates HTML

### 5. Ejecutar la Aplicación

#### Terminal 1 - Backend (FastAPI)
```bash
cd backend
uvicorn app.main:app --reload --port 8001
```

#### Terminal 2 - Frontend (Django)
```bash
cd frontend
python manage.py makemigrations
python manage.py migrate
python manage.py runserver 8000
```

## 🌐 Acceso a la Aplicación

### Frontend (Interfaz de Usuario)
- **URL**: http://localhost:8000/banco/
- **Descripción**: Interfaz web completa para gestión del banco

### Backend (API REST)
- **URL**: http://localhost:8001
- **Documentación API**: http://localhost:8001/docs
- **Descripción**: API REST con documentación interactiva Swagger

## 📡 Endpoints de la API

### Clientes
- `POST /clientes/` - Crear cliente
- `GET /clientes/` - Listar clientes

### Cuentas
- `POST /cuentas/` - Abrir cuenta
- `GET /cuentas/` - Listar cuentas

### Transacciones
- `POST /transacciones/consignar/` - Realizar consignación
- `POST /transacciones/retirar/` - Realizar retiro
- `GET /cuentas/{id}/saldo` - Consultar saldo
- `GET /cuentas/{id}/historial` - Obtener historial

## 🎨 Patrones de Diseño Implementados

### Backend - Patrón Servicio + REST API
```python
# Capa de Servicio (Lógica de Negocio)
BancoService.crear_cliente()
BancoService.realizar_retiro()
BancoService.consultar_saldo()

# Capa de API (Controladores REST)
@app.post("/clientes/")
@app.post("/transacciones/consignar/")
```

### Frontend - Patrón MTV (Model-Template-View)
```python
# Views (Controladores)
def clientes(request)
def transacciones(request)

# Templates (Vistas)
base.html, index.html, clientes.html

# Models (Modelos - opcional)
Cliente, Cuenta, Transaccion
```

## 💼 Métodos de Negocio Implementados

### Validaciones de Negocio
- ✅ Identificación única por cliente
- ✅ Generación automática de números de cuenta
- ✅ Validación de saldo suficiente para retiros
- ✅ Control de cuentas activas/inactivas
- ✅ Registro histórico de transacciones
- ✅ Transacciones atómicas para operaciones críticas

### Reglas del Dominio Bancario
```python
# En services.py
if cuenta.saldo < retiro.monto:
    raise ValueError("Saldo insuficiente")
if not cuenta.activa:
    raise ValueError("Cuenta inactiva")
```

## 🗃️ Estructura de la Base de Datos

### Tabla: clientes
- `id` (PK), `identificacion` (UNIQUE), `nombres`, `email`, `telefono`, `fecha_registro`

### Tabla: cuentas  
- `id` (PK), `cliente_id` (FK), `numero_cuenta` (UNIQUE), `tipo_cuenta`, `saldo`, `activa`

### Tabla: transacciones
- `id` (PK), `cuenta_id` (FK), `tipo`, `monto`, `descripcion`, `fecha_transaccion`, `saldo_anterior`, `saldo_posterior`

Usuario admin creado: admin / admin123
Usuario normal: pepitolopez / 12345678

Cliente de prueba creado: cliente_test / cliente123

usuarios del sistema:
hildebrandoyunado / 123456
aremolina3 / 123456
chancasas1 / 123456


## 🔧 Estructura del Proyecto

```
minibanco/
├── backend/
│   └── app/
│       ├── __init__.py
│       ├── main.py          # Aplicación FastAPI
│       ├── models.py        # Modelos SQLAlchemy
│       ├── schemas.py       # Esquemas Pydantic
│       ├── services.py      # Lógica de negocio
│       └── database.py      # Configuración DB
├── frontend/
│   ├── manage.py
│   ├── frontend/
│   │   ├── settings.py      # Configuración Django
│   │   └── urls.py          # URLs principales
│   └── banco/
│       ├── views.py         # Vistas Django
│       ├── urls.py          # URLs de la app
│       └── templates/banco/ # Templates HTML
└── shared_db/
    └── minibanco.db         # Base de datos SQLite
```

## 🧪 Pruebas y Validación

### Proceso de Prueba Recomendado
1. **Registrar cliente** en http://localhost:8000/banco/clientes/
2. **Abrir cuenta** para el cliente en http://localhost:8000/banco/cuentas/
3. **Realizar transacciones** en http://localhost:8000/banco/transacciones/
4. **Verificar historial** mediante la API en http://localhost:8001/docs

### Validación de Funcionalidades
- ✅ Creación de clientes con identificación única
- ✅ Apertura de múltiples cuentas por cliente
- ✅ Consignaciones y retiros con validación de saldo
- ✅ Consultas de saldo con registro en historial
- ✅ Historial completo de transacciones

## 📈 Características Destacadas

### Seguridad y Validación
- Validación de datos en frontend y backend
- Control de transacciones atómicas
- Prevención de operaciones inválidas

### Experiencia de Usuario
- Interfaz responsive con Bootstrap
- Mensajes de confirmación y error
- Validaciones en tiempo real
- Navegación intuitiva

### Mantenibilidad
- Código modular y bien estructurado
- Separación clara de responsabilidades
- Documentación automática de APIs
- Fácil extensión para nuevas funcionalidades

## 🔮 Posibles Mejoras Futuras

- [ ] Autenticación y autorización de usuarios
- [ ] Reportes y estadísticas financieras
- [ ] Transferencias entre cuentas
- [ ] Notificaciones por email
- [ ] API para terceros
- [ ] Dashboard administrativo

## 👥 Responsable del Desarrollo

**Estudiante:** Anghie Remolina
**Curso:** Desarrollo Web - Eje 3
**Institución:** [Tu Institución]

## 📄 Licencia

Este proyecto es desarrollado con fines académicos como parte de los requisitos del curso de Desarrollo Web.

---

**¡Sistema listo para producción!** 🎉