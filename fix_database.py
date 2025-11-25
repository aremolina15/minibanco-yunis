#!/usr/bin/env python3
"""
Script para corregir los hashes de contraseñas en la base de datos
Convierte de SHA256+salt a bcrypt
"""
import os
import sqlite3
import bcrypt

def fix_passwords():
    db_path = "shared_db/minibanco.db"
    
    if not os.path.exists(db_path):
        print("❌ Base de datos no encontrada")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔧 Corrigiendo hashes de contraseñas...")
    
    # Obtener todos los usuarios
    cursor.execute("SELECT id, username FROM usuarios")
    usuarios = cursor.fetchall()
    
    # Contraseñas por defecto conocidas
    passwords = {
        'admin': 'admin123',
        'cliente_test': 'cliente123'
    }
    
    for user_id, username in usuarios:
        if username in passwords:
            password = passwords[username]
            # Generar hash bcrypt
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Actualizar en la base de datos
            cursor.execute(
                "UPDATE usuarios SET password_hash = ? WHERE id = ?",
                (password_hash, user_id)
            )
            print(f"✅ Hash actualizado para usuario: {username}")
    
    # Eliminar columna salt si existe (no es necesaria con bcrypt)
    try:
        cursor.execute("ALTER TABLE usuarios DROP COLUMN salt")
        print("✅ Columna 'salt' eliminada")
    except sqlite3.OperationalError:
        print("ℹ️  Columna 'salt' no existe o no se pudo eliminar (no es crítico)")
    
    conn.commit()
    conn.close()
    
    print("\n🎉 Contraseñas corregidas!")
    print("\n📋 Credenciales actualizadas:")
    print("   👨‍💼 Admin: admin / admin123")
    print("   👤 Cliente: cliente_test / cliente123")

if __name__ == "__main__":
    fix_passwords()
