#!/usr/bin/env python3
"""
Script de validación completa para la funcionalidad de eliminar usuarios
Verifica Backend, Base de Datos y simula Frontend
"""
import sqlite3
import requests
import json

# Configuración
API_BASE_URL = "http://localhost:8001"
DB_PATH = "shared_db/minibanco.db"

def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def verificar_backend_running():
    """Verifica que el backend esté corriendo"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def login_admin():
    """Hace login como admin y retorna el token"""
    print_section("PASO 1: Login como Admin")
    
    data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/auth/login", json=data)
        if response.status_code == 200:
            result = response.json()
            token = result['access_token']
            print(f"✅ Login exitoso como admin")
            print(f"📝 Token: {token[:50]}...")
            return token
        else:
            print(f"❌ Error en login: {response.status_code}")
            print(f"   Detalle: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Excepción en login: {e}")
        return None

def crear_usuario_prueba(token):
    """Crea un usuario de prueba para eliminar"""
    print_section("PASO 2: Crear Usuario de Prueba")
    
    data = {
        "identificacion": "999999999",
        "tipo_identificacion": "CC",
        "nombres": "Usuario Temporal Test",
        "email": "temporal@test.com",
        "telefono": "3009999999",
        "username": "usuario_temp_test",
        "password": "test123"
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.post(f"{API_BASE_URL}/clientes/", json=data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Usuario creado exitosamente")
            print(f"   ID: {result['id']}")
            print(f"   Username: usuario_temp_test")
            print(f"   Usuario ID: {result['usuario_id']}")
            return result['usuario_id']
        else:
            print(f"❌ Error creando usuario: {response.status_code}")
            print(f"   Detalle: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Excepción creando usuario: {e}")
        return None

def verificar_usuario_en_bd(usuario_id, esperado_activo=True):
    """Verifica el estado del usuario en la base de datos"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, username, activo FROM usuarios WHERE id = ?", (usuario_id,))
    result = cursor.fetchone()
    
    conn.close()
    
    if result:
        id_user, username, activo = result
        estado = "ACTIVO" if activo else "INACTIVO"
        print(f"   BD → Usuario {username} (ID: {id_user}): {estado}")
        return activo == (1 if esperado_activo else 0)
    else:
        print(f"   BD → Usuario ID {usuario_id} NO ENCONTRADO")
        return False

def listar_usuarios_api(token):
    """Lista usuarios desde la API"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{API_BASE_URL}/admin/usuarios/", headers=headers)
        if response.status_code == 200:
            usuarios = response.json()
            return usuarios
        else:
            print(f"❌ Error listando usuarios: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Excepción listando usuarios: {e}")
        return []

def eliminar_usuario_api(token, usuario_id):
    """Elimina (desactiva) un usuario vía API"""
    print_section("PASO 3: Eliminar Usuario vía API")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"🗑️  Intentando eliminar usuario ID: {usuario_id}")
    
    # Verificar estado ANTES
    print("\n📊 Estado ANTES de eliminar:")
    verificar_usuario_en_bd(usuario_id, esperado_activo=True)
    
    try:
        response = requests.delete(
            f"{API_BASE_URL}/admin/usuarios/{usuario_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Respuesta API: {result['mensaje']}")
            
            # Verificar estado DESPUÉS
            print("\n📊 Estado DESPUÉS de eliminar:")
            esta_inactivo = verificar_usuario_en_bd(usuario_id, esperado_activo=False)
            
            if esta_inactivo:
                print("\n✅ VALIDACIÓN EXITOSA: Usuario desactivado correctamente")
                return True
            else:
                print("\n❌ VALIDACIÓN FALLIDA: Usuario NO fue desactivado")
                return False
        else:
            print(f"\n❌ Error en API: {response.status_code}")
            print(f"   Detalle: {response.text}")
            return False
    except Exception as e:
        print(f"\n❌ Excepción eliminando usuario: {e}")
        return False

def intentar_eliminar_admin(token):
    """Intenta eliminar el usuario admin (debe fallar)"""
    print_section("PASO 4: Prueba de Seguridad - Intentar Eliminar Admin")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Primero obtener el ID del usuario admin
    usuarios = listar_usuarios_api(token)
    admin_id = None
    for u in usuarios:
        if u['username'] == 'admin':
            admin_id = u['id']
            break
    
    if not admin_id:
        print("❌ No se encontró el usuario admin")
        return False
    
    print(f"🔒 Intentando eliminar usuario admin (ID: {admin_id})...")
    
    try:
        response = requests.delete(
            f"{API_BASE_URL}/admin/usuarios/{admin_id}",
            headers=headers
        )
        
        if response.status_code == 400:
            error = response.json().get('detail', '')
            print(f"✅ Protección funcionando: {error}")
            return True
        else:
            print(f"❌ ERROR CRÍTICO: Se pudo eliminar admin (código: {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Excepción: {e}")
        return False

def verificar_usuarios_lista_api(token, usuario_id):
    """Verifica que el usuario eliminado NO aparezca en la lista de usuarios activos"""
    print_section("PASO 5: Verificar Lista de Usuarios")
    
    usuarios = listar_usuarios_api(token)
    
    print(f"\n📋 Total de usuarios en lista API: {len(usuarios)}")
    
    # Buscar el usuario eliminado
    usuario_encontrado = None
    for u in usuarios:
        if u['id'] == usuario_id:
            usuario_encontrado = u
            break
    
    if usuario_encontrado:
        if not usuario_encontrado.get('activo', True):
            print(f"✅ Usuario ID {usuario_id} aparece como INACTIVO en la lista")
            return True
        else:
            print(f"❌ Usuario ID {usuario_id} aparece como ACTIVO (debería estar inactivo)")
            return False
    else:
        print(f"✅ Usuario ID {usuario_id} no aparece en la lista de usuarios activos")
        return True

def verificar_login_usuario_inactivo(usuario_id):
    """Intenta hacer login con un usuario inactivo (debe fallar)"""
    print_section("PASO 6: Verificar Login con Usuario Inactivo")
    
    data = {
        "username": "usuario_temp_test",
        "password": "test123"
    }
    
    print("🔐 Intentando login con usuario desactivado...")
    
    try:
        response = requests.post(f"{API_BASE_URL}/auth/login", json=data)
        
        if response.status_code == 401:
            print("✅ Login rechazado correctamente - Usuario inactivo no puede autenticarse")
            return True
        elif response.status_code == 200:
            print("❌ ERROR: Usuario inactivo pudo hacer login")
            return False
        else:
            print(f"⚠️  Respuesta inesperada: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Excepción: {e}")
        return False

def limpiar_usuario_prueba():
    """Elimina permanentemente el usuario de prueba de la BD"""
    print_section("LIMPIEZA: Eliminar Usuario de Prueba")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Obtener usuario_id del cliente
        cursor.execute("SELECT usuario_id FROM clientes WHERE identificacion = '999999999'")
        result = cursor.fetchone()
        
        if result:
            usuario_id = result[0]
            
            # Eliminar cliente
            cursor.execute("DELETE FROM clientes WHERE identificacion = '999999999'")
            print("  🗑️  Cliente eliminado")
            
            # Eliminar usuario
            cursor.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
            print("  🗑️  Usuario eliminado")
            
            conn.commit()
            print("✅ Limpieza completada")
        else:
            print("ℹ️  No se encontró usuario de prueba para limpiar")
    except Exception as e:
        print(f"❌ Error en limpieza: {e}")
    finally:
        conn.close()

def main():
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*20 + "VALIDACIÓN COMPLETA DE CRUD" + " "*20 + "║")
    print("║" + " "*17 + "ELIMINAR USUARIOS DEL SISTEMA" + " "*18 + "║")
    print("╚" + "="*68 + "╝")
    
    # Verificar que el backend esté corriendo
    if not verificar_backend_running():
        print("\n❌ ERROR: El backend no está corriendo en http://localhost:8001")
        print("   Por favor, inicia el backend con:")
        print("   cd minibanco/backend && uvicorn app.main:app --reload --port 8001")
        return
    
    print("\n✅ Backend detectado y corriendo")
    
    # PASO 1: Login
    token = login_admin()
    if not token:
        print("\n❌ No se pudo obtener token de autenticación")
        return
    
    # PASO 2: Crear usuario de prueba
    usuario_id = crear_usuario_prueba(token)
    if not usuario_id:
        print("\n❌ No se pudo crear usuario de prueba")
        return
    
    # PASO 3: Eliminar usuario
    eliminacion_exitosa = eliminar_usuario_api(token, usuario_id)
    
    if not eliminacion_exitosa:
        print("\n❌ La eliminación falló")
        limpiar_usuario_prueba()
        return
    
    # PASO 4: Intentar eliminar admin (debe fallar)
    proteccion_admin = intentar_eliminar_admin(token)
    
    # PASO 5: Verificar en lista
    verificacion_lista = verificar_usuarios_lista_api(token, usuario_id)
    
    # PASO 6: Verificar login bloqueado
    login_bloqueado = verificar_login_usuario_inactivo(usuario_id)
    
    # RESUMEN FINAL
    print_section("RESUMEN DE VALIDACIÓN")
    
    resultados = {
        "Login Admin": "✅" if token else "❌",
        "Crear Usuario": "✅" if usuario_id else "❌",
        "Eliminar Usuario (Soft Delete)": "✅" if eliminacion_exitosa else "❌",
        "Protección Usuario Admin": "✅" if proteccion_admin else "❌",
        "Usuario No Aparece en Lista": "✅" if verificacion_lista else "❌",
        "Login Bloqueado": "✅" if login_bloqueado else "❌"
    }
    
    print("\n📊 Resultados:")
    for prueba, resultado in resultados.items():
        print(f"   {resultado} {prueba}")
    
    exitosas = sum(1 for r in resultados.values() if r == "✅")
    total = len(resultados)
    
    print(f"\n🎯 Total: {exitosas}/{total} pruebas exitosas")
    
    if exitosas == total:
        print("\n🎉 ¡TODAS LAS VALIDACIONES PASARON!")
        print("✅ La funcionalidad de eliminar usuarios funciona correctamente en:")
        print("   • Backend (API)")
        print("   • Base de Datos (Soft Delete)")
        print("   • Seguridad (Protección admin)")
        print("   • Autenticación (Login bloqueado)")
    else:
        print(f"\n⚠️  {total - exitosas} prueba(s) fallaron")
        print("   Revisa los detalles arriba")
    
    # Limpiar
    limpiar_usuario_prueba()
    
    print("\n" + "="*70)

if __name__ == "__main__":
    main()
