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
]