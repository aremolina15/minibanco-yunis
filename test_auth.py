#!/usr/bin/env python3
"""
Script de prueba para verificar autenticación
"""
import sqlite3
import bcrypt

def test_auth():
    db_path = "shared_db/minibanco.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🧪 Probando autenticación...\n")
    
    # Obtener usuario admin
    cursor.execute("SELECT username, password_hash FROM usuarios WHERE username = 'admin'")
    result = cursor.fetchone()
    
    if result:
        username, password_hash = result
        print(f"✅ Usuario encontrado: {username}")
        print(f"📝 Hash almacenado: {password_hash[:50]}...")
        
        # Probar contraseña correcta
        password_test = 'admin123'
        try:
            is_correct = bcrypt.checkpw(password_test.encode('utf-8'), password_hash.encode('utf-8'))
            if is_correct:
                print(f"✅ Contraseña '{password_test}' es CORRECTA")
            else:
                print(f"❌ Contraseña '{password_test}' es INCORRECTA")
        except Exception as e:
            print(f"❌ Error al verificar: {e}")
        
        # Probar contraseña incorrecta
        password_wrong = 'wrongpass'
        try:
            is_wrong = bcrypt.checkpw(password_wrong.encode('utf-8'), password_hash.encode('utf-8'))
            if not is_wrong:
                print(f"✅ Contraseña incorrecta '{password_wrong}' rechazada correctamente")
        except Exception as e:
            print(f"❌ Error al verificar: {e}")
    else:
        print("❌ Usuario admin no encontrado")
    
    # Probar cliente_test
    print("\n🧪 Probando cliente_test...\n")
    cursor.execute("SELECT username, password_hash FROM usuarios WHERE username = 'cliente_test'")
    result = cursor.fetchone()
    
    if result:
        username, password_hash = result
        print(f"✅ Usuario encontrado: {username}")
        
        password_test = 'cliente123'
        try:
            is_correct = bcrypt.checkpw(password_test.encode('utf-8'), password_hash.encode('utf-8'))
            if is_correct:
                print(f"✅ Contraseña '{password_test}' es CORRECTA")
            else:
                print(f"❌ Contraseña '{password_test}' es INCORRECTA")
        except Exception as e:
            print(f"❌ Error al verificar: {e}")
    
    conn.close()
    
    print("\n" + "="*50)
    print("✅ Pruebas completadas!")
    print("="*50)

if __name__ == "__main__":
    test_auth()
