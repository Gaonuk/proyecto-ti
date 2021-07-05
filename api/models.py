from django.db import models
from datetime import datetime
from django.contrib.postgres.fields import ArrayField

# Create your models here.

class Log(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    mensaje = models.TextField()

class RecievedOC(models.Model):
    id = models.TextField(primary_key=True)
    cliente = models.TextField()
    proveedor = models.TextField()
    sku = models.IntegerField()
    fecha_entrega = models.DateTimeField()
    cantidad = models.IntegerField()
    cantidad_despachada = models.IntegerField(default=0)
    precio_unitario = models.IntegerField()
    canal = models.CharField(max_length=3)
    estado = models.CharField(max_length=10)
    notas = models.TextField(blank=True)
    rechazo = models.TextField(blank=True)
    anulacion = models.TextField(blank=True)
    url_notification = models.TextField(blank=True)
    created_at = models.DateTimeField()
    updated_at =  models.DateTimeField()


class SentOC(models.Model):
    id = models.TextField(primary_key=True)
    cliente = models.TextField()
    proveedor = models.TextField()
    sku = models.IntegerField()
    fecha_entrega = models.DateTimeField()
    cantidad = models.IntegerField()
    cantidad_despachada = models.IntegerField(default=0)
    precio_unitario = models.IntegerField()
    canal = models.CharField(max_length=3)
    estado = models.CharField(max_length=10)
    notas = models.TextField(blank=True)
    rechazo = models.TextField(blank=True)
    anulacion = models.TextField(blank=True)
    url_notification = models.TextField(blank=True)
    created_at = models.DateTimeField()
    updated_at =  models.DateTimeField()

# class Lote(models.Model):
#     sku_numlote = models.CharField(primary_key=True, max_length=256)
#     sku = models.CharField(max_length=10)
#     fecha_vencimiento = models.DateTimeField()
#     cantidad_disponible = models.IntegerField()
#     productos = ArrayField(models.CharField(max_length=256))

class ProductoBodega(models.Model):
    id = models.CharField(primary_key=True, max_length=100)
    sku = models.CharField(max_length=15)
    almacen = models.CharField(max_length=50)
    fecha_vencimiento = models.DateTimeField()
    # lote = models.ForeignKey(Lote, on_delete=models.CASCADE,)
    oc_reservada = models.TextField(default=None) # Este atributo es el ID de la RecievedOC con la que se reservó el producto.

class Pedido(models.Model):
    id = models.CharField(primary_key=True, max_length=100)
    sku = models.CharField(max_length=15)
    cantidad = models.IntegerField()
    fecha_disponible = models.DateTimeField()
    disponbile_para_uso = models.BooleanField(default=True)

class ProductoDespachado(models.Model):
    id = models.CharField(primary_key=True, max_length=100)
    sku = models.CharField(max_length=15)
    cliente = models.CharField(max_length=30)
    oc_cliente = models.CharField(max_length=40)
    precio = models.IntegerField()

