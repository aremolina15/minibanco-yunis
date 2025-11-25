import requests
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import JsonResponse
from django.contrib import messages
import json

def index(request):
    """Página principal del banco"""
    usuario = request.session.get('usuario', None)
    context = {
        'api_base': settings.API_BASE_URL,
        'usuario': usuario
    }
    return render(request, 'banco/index.html', context)

def login_view(request):
    """Vista para iniciar sesión"""
    if request.method == 'POST':
        try:
            data = {
                'username': request.POST.get('username'),
                'password': request.POST.get('password')
            }
            
            response = requests.post(f"{settings.API_BASE_URL}/auth/login", json=data)
            
            if response.status_code == 200:
                result = response.json()
                # Guardar en sesión
                request.session['access_token'] = result['access_token']
                request.session['usuario'] = result['usuario']
                request.session.set_expiry(86400)  # 24 horas
                
                messages.success(request, f"Bienvenido, {result['usuario']['nombres'] or result['usuario']['username']}!")
                
                # Redirigir según el tipo de usuario
                if result['usuario']['tipo'] == 'admin':
                    return redirect('banco:admin_dashboard')
                else:
                    return redirect('banco:cliente_dashboard')
            else:
                error_detail = response.json().get('detail', 'Credenciales incorrectas')
                messages.error(request, f'Error: {error_detail}')
                
        except Exception as e:
            messages.error(request, f'Error de conexión: {str(e)}')
    
    return render(request, 'banco/login.html')

def registro_view(request):
    """Vista para registro de nuevos clientes"""
    if request.method == 'POST':
        try:
            data = {
                'identificacion': request.POST.get('identificacion'),
                'tipo_identificacion': request.POST.get('tipo_identificacion', 'CC'),
                'nombres': request.POST.get('nombres'),
                'email': request.POST.get('email'),
                'telefono': request.POST.get('telefono'),
                'username': request.POST.get('username'),
                'password': request.POST.get('password')
            }
            
            response = requests.post(f"{settings.API_BASE_URL}/auth/registro", json=data)
            
            if response.status_code == 200:
                result = response.json()
                # Guardar en sesión automáticamente
                request.session['access_token'] = result['access_token']
                request.session['usuario'] = result['usuario']
                request.session.set_expiry(86400)
                
                messages.success(request, '¡Registro exitoso! Bienvenido a Minibanco.')
                return redirect('banco:cliente_dashboard')
            else:
                error_detail = response.json().get('detail', 'Error en el registro')
                messages.error(request, f'Error: {error_detail}')
                
        except Exception as e:
            messages.error(request, f'Error de conexión: {str(e)}')
    
    return render(request, 'banco/registro.html')

def logout_view(request):
    """Cerrar sesión"""
    request.session.flush()
    messages.success(request, 'Sesión cerrada correctamente.')
    return redirect('banco:index')

def admin_dashboard(request):
    """Dashboard para administradores"""
    usuario = request.session.get('usuario')
    if not usuario or usuario.get('tipo') != 'admin':
        messages.error(request, 'Acceso denegado. Se requieren privilegios de administrador.')
        return redirect('banco:login')
    
    # Obtener estadísticas
    token = request.session.get('access_token')
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        clientes_response = requests.get(f"{settings.API_BASE_URL}/clientes/", headers=headers)
        cuentas_response = requests.get(f"{settings.API_BASE_URL}/cuentas/", headers=headers)
        
        clientes = clientes_response.json() if clientes_response.status_code == 200 else []
        cuentas = cuentas_response.json() if cuentas_response.status_code == 200 else []
        
    except Exception as e:
        clientes = []
        cuentas = []
        messages.error(request, f'Error al cargar datos: {str(e)}')
    
    context = {
        'usuario': usuario,
        'total_clientes': len(clientes),
        'total_cuentas': len(cuentas),
        'clientes': clientes[:5]  # Últimos 5 clientes
    }
    return render(request, 'banco/admin_dashboard.html', context)

def cliente_dashboard(request):
    """Dashboard para clientes"""
    usuario = request.session.get('usuario')
    if not usuario:
        messages.error(request, 'Debes iniciar sesión para acceder a esta página.')
        return redirect('banco:login')
    
    # Verificar que el usuario sea cliente
    if usuario.get('tipo') != 'cliente':
        messages.error(request, 'Esta sección es solo para clientes.')
        return redirect('banco:index')
    
    token = request.session.get('access_token')
    headers = {'Authorization': f'Bearer {token}'}
    
    cuentas = []
    total_cuentas = 0
    saldo_total = 0.0
    cuenta_mayor_saldo = None
    
    try:
        # Obtener cuentas del usuario
        response = requests.get(f"{settings.API_BASE_URL}/mis-cuentas/todas", headers=headers)
        
        if response.status_code == 200:
            cuentas = response.json()
            print(f"🔍 Cuentas obtenidas: {cuentas}")  # Debug
            
            # Calcular estadísticas
            total_cuentas = len(cuentas)
            
            # Sumar saldos
            for cuenta in cuentas:
                saldo = cuenta.get('saldo', 0)
                # Asegurarnos de que el saldo sea numérico
                if isinstance(saldo, str):
                    try:
                        saldo = float(saldo)
                    except (ValueError, TypeError):
                        saldo = 0.0
                saldo_total += saldo
            
            # Encontrar cuenta con mayor saldo
            if cuentas:
                cuenta_mayor_saldo = max(cuentas, key=lambda x: float(x.get('saldo', 0)))
                
        elif response.status_code == 403:
            messages.error(request, 'No tienes permisos para ver cuentas.')
        elif response.status_code == 404:
            messages.info(request, 'No se encontró información de cliente.')
        else:
            messages.error(request, 'Error al cargar las cuentas.')
            
    except requests.exceptions.ConnectionError:
        messages.error(request, 'Error de conexión con el servidor.')
    except Exception as e:
        messages.error(request, f'Error inesperado: {str(e)}')
        print(f"❌ Error en cliente_dashboard: {e}")  # Debug
    
    context = {
        'usuario': usuario,
        'cuentas': cuentas,
        'total_cuentas': total_cuentas,
        'saldo_total': saldo_total,
        'cuenta_mayor_saldo': cuenta_mayor_saldo,
    }
    return render(request, 'banco/cliente_dashboard.html', context)

# Vistas existentes actualizadas para usar autenticación
def clientes(request):
    """Gestión de clientes (solo admin)"""
    usuario = request.session.get('usuario')
    if not usuario or usuario.get('tipo') != 'admin':
        messages.error(request, 'Acceso denegado. Se requieren privilegios de administrador.')
        return redirect('banco:login')
    
    token = request.session.get('access_token')
    headers = {'Authorization': f'Bearer {token}'}
    
    if request.method == 'POST':
        try:
            # Asegurarse de que todos los campos estén presentes
            data = {
                'identificacion': request.POST.get('identificacion', '').strip(),
                'nombres': request.POST.get('nombres', '').strip(),
                'email': request.POST.get('email', '').strip(),
                'telefono': request.POST.get('telefono', '').strip(),
                'tipo_identificacion': request.POST.get('tipo_identificacion', 'CC'),
                'username': request.POST.get('username', '').strip(),
                'password': request.POST.get('password', '').strip()
            }
            
            # Validar que ningún campo requerido esté vacío
            campos_requeridos = ['identificacion', 'nombres', 'email', 'telefono', 'username', 'password']
            for campo in campos_requeridos:
                if not data[campo]:
                    messages.error(request, f'El campo {campo} es requerido')
                    return redirect('banco:clientes')
            
            print(f"Enviando datos al backend: {data}")  # Para debug
            
            response = requests.post(f"{settings.API_BASE_URL}/clientes/", json=data)
            
            if response.status_code == 200:
                messages.success(request, 'Cliente creado exitosamente')
                return redirect('banco:clientes')
            else:
                error_detail = response.json().get('detail', 'Error desconocido')
                messages.error(request, f'Error: {error_detail}')
                
        except Exception as e:
            messages.error(request, f'Error de conexión: {str(e)}')
    
    # Obtener lista de clientes
    try:
        response = requests.get(f"{settings.API_BASE_URL}/clientes/", headers=headers)
        if response.status_code == 200:
            clientes = response.json()
        else:
            clientes = []
            messages.error(request, 'Error al obtener clientes')
    except:
        clientes = []
        messages.error(request, 'Error de conexión al cargar clientes')
    
    return render(request, 'banco/clientes.html', {
        'clientes': clientes,
        'usuario': usuario
    })

def cuentas(request):
    """Gestión de cuentas bancarias (solo admin)"""
    usuario = request.session.get('usuario')
    if not usuario or usuario.get('tipo') != 'admin':
        messages.error(request, 'Acceso denegado. Se requieren privilegios de administrador.')
        return redirect('banco:login')
    
    token = request.session.get('access_token')
    headers = {'Authorization': f'Bearer {token}'}
    
    if request.method == 'POST':
        try:
            data = {
                'cliente_id': int(request.POST.get('cliente_id')),
                'tipo_cuenta': request.POST.get('tipo_cuenta'),
                'saldo_inicial': float(request.POST.get('saldo_inicial', 0))
            }
            
            response = requests.post(f"{settings.API_BASE_URL}/cuentas/", json=data, headers=headers)
            
            if response.status_code == 200:
                messages.success(request, 'Cuenta abierta exitosamente')
                return redirect('banco:cuentas')
            else:
                error_detail = response.json().get('detail', 'Error desconocido')
                messages.error(request, f'Error: {error_detail}')
                
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    # Obtener datos
    try:
        cuentas_response = requests.get(f"{settings.API_BASE_URL}/cuentas/", headers=headers)
        clientes_response = requests.get(f"{settings.API_BASE_URL}/clientes/", headers=headers)
        
        cuentas = cuentas_response.json() if cuentas_response.status_code == 200 else []
        clientes = clientes_response.json() if clientes_response.status_code == 200 else []
        
    except Exception as e:
        cuentas = []
        clientes = []
        messages.error(request, f'Error de conexión: {str(e)}')
    
    context = {
        'cuentas': cuentas,
        'clientes': clientes,
        'usuario': usuario
    }
    return render(request, 'banco/cuentas.html', context)

def transacciones(request):
    """Realizar transacciones bancarias"""
    usuario = request.session.get('usuario')
    if not usuario:
        messages.error(request, 'Debes iniciar sesión para realizar transacciones.')
        return redirect('banco:login')
    
    token = request.session.get('access_token')
    headers = {'Authorization': f'Bearer {token}'}
    
    if request.method == 'POST':
        try:
            tipo = request.POST.get('tipo')
            cuenta_id = int(request.POST.get('cuenta_id'))
            monto = float(request.POST.get('monto', 0))
            descripcion = request.POST.get('descripcion', '')
            
            if tipo == 'CONSIGNACION':
                data = {
                    'cuenta_id': cuenta_id, 
                    'monto': monto, 
                    'descripcion': descripcion
                }
                response = requests.post(f"{settings.API_BASE_URL}/transacciones/consignar/", json=data, headers=headers)
            elif tipo == 'RETIRO':
                data = {
                    'cuenta_id': cuenta_id, 
                    'monto': monto, 
                    'descripcion': descripcion
                }
                response = requests.post(f"{settings.API_BASE_URL}/transacciones/retirar/", json=data, headers=headers)
            else:
                messages.error(request, 'Tipo de transacción no válido')
                return redirect('banco:transacciones')
            
            if response.status_code == 200:
                result = response.json()
                messages.success(request, 
                    f"{result.get('mensaje', 'Transacción exitosa')}. "
                    f"Nuevo saldo: ${result.get('nuevo_saldo', 0):.2f}"
                )
                return redirect('banco:transacciones')
            else:
                error_detail = response.json().get('detail', 'Error desconocido')
                messages.error(request, f'Error: {error_detail}')
                
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    # Obtener cuentas según el tipo de usuario - CORREGIDO
    try:
        if usuario.get('tipo') == 'admin':
            cuentas_response = requests.get(f"{settings.API_BASE_URL}/cuentas/", headers=headers)
        else:
            # Usar el mismo endpoint que en cliente_dashboard
            cuentas_response = requests.get(f"{settings.API_BASE_URL}/mis-cuentas/todas", headers=headers)
            
        if cuentas_response.status_code == 200:
            cuentas = cuentas_response.json()
            print(f"🔍 Cuentas en transacciones: {cuentas}")  # Debug
        else:
            cuentas = []
            messages.error(request, 'Error al cargar las cuentas')
    except Exception as e:
        cuentas = []
        messages.error(request, f'Error al cargar las cuentas: {str(e)}')
        print(f"❌ Error en transacciones: {e}")  # Debug
    
    return render(request, 'banco/transacciones.html', {
        'cuentas': cuentas,
        'usuario': usuario
    })

def consultar_saldo(request):
    """Consultar saldo de una cuenta"""
    usuario = request.session.get('usuario')
    if not usuario:
        messages.error(request, 'Debes iniciar sesión para consultar saldos.')
        return redirect('banco:login')
    
    if request.method == 'POST':
        try:
            cuenta_id = int(request.POST.get('cuenta_id'))
            token = request.session.get('access_token')
            headers = {'Authorization': f'Bearer {token}'}
            
            response = requests.get(f"{settings.API_BASE_URL}/cuentas/{cuenta_id}/saldo", headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                messages.success(
                    request, 
                    f"Saldo de cuenta {result.get('numero_cuenta')}: "
                    f"${result.get('saldo', 0):.2f}"
                )
            else:
                error_detail = response.json().get('detail', 'Error desconocido')
                messages.error(request, f'Error: {error_detail}')
                
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    return redirect('banco:transacciones')

def historial_json(request, cuenta_id):
    """API para obtener historial de transacciones"""
    usuario = request.session.get('usuario')
    if not usuario:
        return JsonResponse({'error': 'No autenticado'}, status=401)
    
    try:
        token = request.session.get('access_token')
        headers = {'Authorization': f'Bearer {token}'}
        
        response = requests.get(f"{settings.API_BASE_URL}/cuentas/{cuenta_id}/historial", headers=headers)
        if response.status_code == 200:
            return JsonResponse({'transacciones': response.json()})
        return JsonResponse({'error': 'Error al obtener historial'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Error de conexión: {str(e)}'}, status=500)
    
def abrir_cuenta_view(request):
    """Vista para que clientes abran cuentas"""
    usuario = request.session.get('usuario')
    if not usuario or usuario.get('tipo') != 'cliente':
        messages.error(request, 'Solo los clientes pueden abrir cuentas.')
        return redirect('banco:login')
    
    token = request.session.get('access_token')
    headers = {'Authorization': f'Bearer {token}'}
    
    if request.method == 'POST':
        try:
            data = {
                'tipo_cuenta': request.POST.get('tipo_cuenta'),
                'saldo_inicial': float(request.POST.get('saldo_inicial', 0))
            }
            
            response = requests.post(
                f"{settings.API_BASE_URL}/mis-cuentas/abrir", 
                json=data, 
                headers=headers
            )
            
            if response.status_code == 200:
                cuenta = response.json()
                messages.success(
                    request, 
                    f'✅ Cuenta {cuenta["tipo_cuenta"]} abierta exitosamente. '
                    f'Número: {cuenta["numero_cuenta"]}'
                )
                return redirect('banco:cliente_dashboard')
            else:
                error_detail = response.json().get('detail', 'Error desconocido')
                messages.error(request, f'Error: {error_detail}')
                
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    return render(request, 'banco/abrir_cuenta.html', {'usuario': usuario})

def transferir_view(request):
    """Vista para transferencias entre cuentas"""
    usuario = request.session.get('usuario')
    if not usuario:
        messages.error(request, 'Debes iniciar sesión para realizar transferencias.')
        return redirect('banco:login')
    
    token = request.session.get('access_token')
    headers = {'Authorization': f'Bearer {token}'}
    
    # Obtener cuentas del usuario - CORREGIDO
    try:
        response = requests.get(f"{settings.API_BASE_URL}/mis-cuentas/todas", headers=headers)
        if response.status_code == 200:
            cuentas = response.json()
            print(f"🔍 Cuentas en transferir: {cuentas}")  # Debug
        else:
            cuentas = []
            messages.error(request, 'Error al cargar las cuentas')
    except Exception as e:
        cuentas = []
        messages.error(request, f'Error al cargar las cuentas: {str(e)}')
        print(f"❌ Error en transferir: {e}")  # Debug
    
    if request.method == 'POST':
        try:
            data = {
                'cuenta_origen_id': int(request.POST.get('cuenta_origen_id')),
                'cuenta_destino_id': int(request.POST.get('cuenta_destino_id')),
                'monto': float(request.POST.get('monto', 0)),
                'descripcion': request.POST.get('descripcion', 'Transferencia entre cuentas')
            }
            
            # Validaciones básicas
            if data['cuenta_origen_id'] == data['cuenta_destino_id']:
                messages.error(request, 'No puedes transferir a la misma cuenta')
                return redirect('banco:transferir')
            
            if data['monto'] <= 0:
                messages.error(request, 'El monto debe ser mayor a cero')
                return redirect('banco:transferir')
            
            response = requests.post(
                f"{settings.API_BASE_URL}/transacciones/transferir/", 
                json=data, 
                headers=headers
            )
            
            if response.status_code == 200:
                resultado = response.json()
                messages.success(
                    request, 
                    f'✅ Transferencia exitosa. '
                    f'De {resultado["cuenta_origen"]} a {resultado["cuenta_destino"]}. '
                    f'Monto: ${resultado["monto"]:.2f}'
                )
                return redirect('banco:cliente_dashboard')
            else:
                error_detail = response.json().get('detail', 'Error desconocido')
                messages.error(request, f'Error: {error_detail}')
                
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    return render(request, 'banco/transferir.html', {
        'cuentas': cuentas,
        'usuario': usuario
    })