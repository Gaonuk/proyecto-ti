from typing import Optional
from django import forms
from requests.api import options
OPCIONES_VACUNAS = [
    ('10001', 'Pfizer'),
    ('10002', 'Sinovac'),
    ('10005', 'Moderna')
]

class FormCambiarAlmacen(forms.Form):
    productoId = forms.CharField(label='ID Producto', max_length=100)
    almacenId = forms.CharField(label='ID Almacen', max_length=100)

class FormCambiarAlmacenPorSKU(forms.Form):
    almacen_origen= forms.CharField(label='Almacén origen', max_length=100)
    SKU = forms.CharField(label='SKU', max_length=100)
    almacenId = forms.CharField(label='ID Almacen destino interno', max_length=100)
    cant_SKU = forms.IntegerField(label= 'cantidad' )

class FormCambiarBodega(forms.Form):
    productoId = forms.CharField(label='ID Producto (Debe estar en despacho)', max_length=100)
    almacenId_externo = forms.CharField(label='ID Almacen Destino externo', max_length=100)
    oc =  forms.CharField(label='ID Orden de Compra', max_length=100, initial="4af9f23d8ead0e1d32000000")
    precio = forms.IntegerField(label= 'Precio de venta (solo números)' )

class FormFabricar(forms.Form):
    SKU = forms.CharField(label='SKU', max_length=100)
    cantidad = forms.IntegerField(label= 'cantidad' )

class FormCrearOC(forms.Form):
    proveedor = forms.CharField(label='Id de proveedor: Grupo que recibe la OC.')
    SKU = forms.CharField(label='SKU', max_length=100)
    fechaEntrega = forms.CharField(label="Fecha solicitada para la entrega de los productos (DD/MM/YYYY;HH:MM:SS)")
    cantidad = forms.IntegerField(label= 'cantidad' )
    precio = forms.IntegerField(label= 'Precio unitario de los productos que se están comprando' )
    canal = forms.CharField(label='Canal donde se está realizando la transacción. (b2b o b2c)')
    notas = forms.CharField(label="Notas adicionales a la OC.", required=False)
    urlNotificacion = forms.CharField(label='Url de notificacion de aceptación o rechazo de la OC.', required=False)

class FormCrearVacuna(forms.Form):
    tipo = forms.CharField(label='Selecciona un tipo de vacuna', widget=forms.Select(choices=OPCIONES_VACUNAS))

class FormActualizarMaxOCIngredientes(forms.Form):
    max_ing = forms.IntegerField(label= 'Max OC de ingredientes aceptadas al mismo tiempo')

class FormActualizarMaxOCVacunas(forms.Form):
    max_vac = forms.IntegerField(label= 'Max OC de vacunas aceptadas al mismo tiempo')