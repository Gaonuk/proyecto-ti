from django import forms

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

