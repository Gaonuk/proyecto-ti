from django.db import models
from datetime import datetime
from django.contrib.postgres.fields import ArrayField

# Create your models here.

class AlgunModelo(models.Model):
    id = models.CharField(primary_key=True, max_length=22)
    name = models.CharField(max_length=50)
    age = models.IntegerField()

class Lote(models.Model):
    sku_numlote = models.CharField(primary_key=True, max_length=256)
    sku = models.CharField(max_length=10)
    fecha_vencimiento = models.DateTimeField()
    cantidad_disponible = models.IntegerField()
    productos = ArrayField(models.CharField(max_length=256))

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
    url_notificaion = models.TextField(blank=True)
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
    url_notificaion = models.TextField(blank=True)
    created_at = models.DateTimeField()
    updated_at =  models.DateTimeField()