from django.urls import path
from . import views

app_name = 'banco'

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('logout/', views.logout_view, name='logout'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('cliente/dashboard/', views.cliente_dashboard, name='cliente_dashboard'),
    path('clientes/', views.clientes, name='clientes'),
    path('cuentas/', views.cuentas, name='cuentas'),
    path('transacciones/', views.transacciones, name='transacciones'),
    path('consultar-saldo/', views.consultar_saldo, name='consultar_saldo'),
    path('abrir-cuenta/', views.abrir_cuenta_view, name='abrir_cuenta'),
    path('transferir/', views.transferir_view, name='transferir'),
    path('api/historial/<int:cuenta_id>/', views.historial_json, name='historial_json'),
    
    # CRUD Usuarios (Admin)
    path('admin/usuarios/', views.admin_usuarios, name='admin_usuarios'),
    path('admin/usuarios/<int:usuario_id>/editar/', views.admin_editar_usuario, name='admin_editar_usuario'),
    path('admin/usuarios/<int:usuario_id>/eliminar/', views.admin_eliminar_usuario, name='admin_eliminar_usuario'),
    
    # CRUD Clientes (Admin)
    path('admin/clientes/<int:cliente_id>/editar/', views.admin_editar_cliente, name='admin_editar_cliente'),
    path('admin/clientes/<int:cliente_id>/eliminar/', views.admin_eliminar_cliente, name='admin_eliminar_cliente'),
    
    # CRUD Cuentas (Admin)
    path('admin/cuentas/<int:cuenta_id>/editar/', views.admin_editar_cuenta, name='admin_editar_cuenta'),
    path('admin/cuentas/<int:cuenta_id>/eliminar/', views.admin_eliminar_cuenta, name='admin_eliminar_cuenta'),
    
    # CRUD Transacciones (Admin)
    path('admin/transacciones/', views.admin_transacciones, name='admin_transacciones'),
    path('admin/transacciones/<int:transaccion_id>/editar/', views.admin_editar_transaccion, name='admin_editar_transaccion'),
    path('admin/transacciones/<int:transaccion_id>/eliminar/', views.admin_eliminar_transaccion, name='admin_eliminar_transaccion'),
]