#!/usr/bin/env python3
import os
import sqlite3
import bcrypt

def reset_database():
    # Ruta de la base de datos
    db_path = "shared_db/minibanco.db"
    
    # Eliminar base de datos existente
    if os.path.exists(db_path):
        os.remove(db_path)
        print("🗑️  Base de datos eliminada")
    
    # Crear directorio si no existe
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Conectar y crear tablas
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔧 Creando tablas...")
    
    # Tabla de usuarios
    cursor.execute('''
        CREATE TABLE usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            salt VARCHAR(32) NOT NULL,
            tipo VARCHAR(20) NOT NULL,
            identificacion VARCHAR(20) UNIQUE,
            nombres VARCHAR(100),
            email VARCHAR(100),
            telefono VARCHAR(15),
            fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
            activo BOOLEAN DEFAULT 1
        )
    ''')
    
    # Tabla de clientes
    cursor.execute('''
        CREATE TABLE clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            identificacion VARCHAR(20) UNIQUE NOT NULL,
            tipo_identificacion VARCHAR(2) DEFAULT 'CC',
            nombres VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL,
            telefono VARCHAR(15) NOT NULL,
            fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    ''')
    
    # Tabla de cuentas
    cursor.execute('''
        CREATE TABLE cuentas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            numero_cuenta VARCHAR(20) UNIQUE NOT NULL,
            tipo_cuenta VARCHAR(10) NOT NULL,
            saldo DECIMAL(15, 2) DEFAULT 0,
            fecha_apertura DATETIME DEFAULT CURRENT_TIMESTAMP,
            activa BOOLEAN DEFAULT 1,
            FOREIGN KEY (cliente_id) REFERENCES clientes (id)
        )
    ''')
    
    # Tabla de transacciones
    cursor.execute('''
        CREATE TABLE transacciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cuenta_id INTEGER NOT NULL,
            tipo VARCHAR(12) NOT NULL,
            monto DECIMAL(15, 2),
            descripcion TEXT,
            fecha_transaccion DATETIME DEFAULT CURRENT_TIMESTAMP,
            saldo_anterior DECIMAL(15, 2) NOT NULL,
            saldo_posterior DECIMAL(15, 2) NOT NULL,
            FOREIGN KEY (cuenta_id) REFERENCES cuentas (id)
        )
    ''')
    
    print("✅ Tablas creadas")
    
    # Crear usuario admin
    print("👤 Creando usuario admin...")
    password_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    cursor.execute('''
        INSERT INTO usuarios (username, password_hash, salt, tipo, nombres, email)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', ('admin', password_hash, 'salt_admin', 'admin', 'Administrador del Sistema', 'admin@minibanco.com'))
    
    # Crear usuario cliente de prueba
    print("👤 Creando cliente de prueba...")
    password_hash_cliente = bcrypt.hashpw('cliente123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    cursor.execute('''
        INSERT INTO usuarios (username, password_hash, salt, tipo, identificacion, nombres, email, telefono)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', ('cliente_test', password_hash_cliente, 'salt_cliente', 'cliente', '123456789', 'Cliente de Prueba', 'cliente@test.com', '3001234567'))
    
    usuario_id = cursor.lastrowid
    
    # Crear cliente asociado
    cursor.execute('''
        INSERT INTO clientes (usuario_id, identificacion, tipo_identificacion, nombres, email, telefono)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (usuario_id, '123456789', 'CC', 'Cliente de Prueba', 'cliente@test.com', '3001234567'))
    
    cliente_id = cursor.lastrowid
    
    # Crear cuentas de prueba
    print("💳 Creando cuentas de prueba...")
    cursor.execute('''
        INSERT INTO cuentas (cliente_id, numero_cuenta, tipo_cuenta, saldo)
        VALUES (?, ?, ?, ?)
    ''', (cliente_id, '1000000001', 'AHORROS', 1000000.00))
    
    cursor.execute('''
        INSERT INTO cuentas (cliente_id, numero_cuenta, tipo_cuenta, saldo)
        VALUES (?, ?, ?, ?)
    ''', (cliente_id, '1000000002', 'CORRIENTE', 500000.00))
    
    # Registrar transacciones iniciales
    print("📝 Creando transacciones de prueba...")
    cursor.execute('''
        INSERT INTO transacciones (cuenta_id, tipo, monto, descripcion, saldo_anterior, saldo_posterior)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (1, 'CONSIGNACION', 1000000.00, 'Apertura de cuenta', 0, 1000000.00))
    
    cursor.execute('''
        INSERT INTO transacciones (cuenta_id, tipo, monto, descripcion, saldo_anterior, saldo_posterior)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (2, 'CONSIGNACION', 500000.00, 'Apertura de cuenta', 0, 500000.00))
    
    # Guardar cambios
    conn.commit()
    conn.close()
    
    print("🎉 Base de datos recreada exitosamente!")
    print("\n📋 Credenciales por defecto:")
    print("   👨‍💼 Admin: admin / admin123")
    print("   👤 Cliente: cliente_test / cliente123")
    print("   💰 Cuentas: 1000000001 (Ahorros - $1,000,000) y 1000000002 (Corriente - $500,000)")

if __name__ == "__main__":
    reset_database()