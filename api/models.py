from django.db import models
from datetime import datetime
from django.contrib.postgres.fields import ArrayField

# Create your models here.

class AlgunModelo(models.Model):
    id = models.CharField(primary_key=True, max_length=100, editable=False)
    name = models.CharField(max_length=50)
    age = models.IntegerField()

class Lote(models.Model):
    sku_numlote = models.CharField(primary_key=True, max_length=256)
    sku = models.CharField(max_length=10)
    fecha_vencimiento = models.DateTimeField()
    cantidad_disponible = models.IntegerField()
    productos = ArrayField(models.CharField(max_length=256))

class ProductoBodega(models.Model):
    id = models.CharField(primary_key=True, max_length=22)
    sku = models.CharField(max_length=10)
    almacen = models.CharField(max_length=15)
    fecha_vencimiento = models.DateTimeField()
    lote = models.ForeignKey(Lote, on_delete=models.CASCADE,)

class Pedido(models.Model):
    id = models.CharField(primary_key=True, max_length=22)
    sku = models.CharField(max_length=10)
    cantidad = models.IntegerField()
    fecha_disponible = models.DateTimeField()

class ProductoDespachado(models.Model):
    id = models.CharField(primary_key=True, max_length=22)
    sku = models.CharField(max_length=10)
    cliente = models.CharField(max_length=20)
    oc_cliente = models.CharField(max_length=25)
    precio = models.IntegerField()

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