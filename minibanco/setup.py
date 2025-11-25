import os
import subprocess
import sys

def setup_project():
    print("=== CONFIGURACIÓN DEL PROYECTO MINIBANCO ===")
    
    # Crear directorios
    print("Creando estructura de directorios...")
    os.makedirs("shared_db", exist_ok=True)
    os.makedirs("backend/app", exist_ok=True)
    os.makedirs("frontend/banco/templates/banco", exist_ok=True)
    
    # Instalar dependencias del backend
    print("Instalando dependencias del backend...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "fastapi==0.104.1", "uvicorn==0.24.0", "sqlalchemy==1.4.46", "pydantic==2.5.0"])
    
    # Instalar dependencias del frontend
    print("Instalando dependencias del frontend...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Django==4.2.7", "requests==2.31.0"])
    
    print("✅ Configuración completada exitosamente!")
    print("\nPara ejecutar el proyecto:")
    print("1. Terminal 1 (Backend): cd backend && uvicorn app.main:app --reload --port 8001")
    print("2. Terminal 2 (Frontend): cd frontend && python manage.py runserver 8000")
    print("3. Abrir en navegador: http://localhost:8000")

if __name__ == "__main__":
    setup_project()