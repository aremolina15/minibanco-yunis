from django.db import models

# Los modelos están en FastAPI, Django solo los usa para migraciones iniciales
class Cliente(models.Model):
    identificacion = models.CharField(max_length=20, unique=True)
    tipo_identificacion = models.CharField(max_length=2, default='CC')
    nombres = models.CharField(max_length=100)
    email = models.EmailField()
    telefono = models.CharField(max_length=15)
    fecha_registro = models.DateTimeField(auto_now_add=True)

class Cuenta(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    numero_cuenta = models.CharField(max_length=20, unique=True)
    tipo_cuenta = models.CharField(max_length=10)
    saldo = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    fecha_apertura = models.DateTimeField(auto_now_add=True)
    activa = models.BooleanField(default=True)

class Transaccion(models.Model):
    cuenta = models.ForeignKey(Cuenta, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=12)
    monto = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    descripcion = models.TextField(blank=True)
    fecha_transaccion = models.DateTimeField(auto_now_add=True)
    saldo_anterior = models.DecimalField(max_digits=15, decimal_places=2)
    saldo_posterior = models.DecimalField(max_digits=15, decimal_places=2)