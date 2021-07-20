from django.contrib import admin
from .models import SentOC, RecievedOC, Log,ProductoBodega, Pedido, ProductoDespachado, CantidadMaxAceptada
# Register your models here.
admin.site.register(SentOC)
admin.site.register(RecievedOC)
admin.site.register(Log)
admin.site.register(ProductoBodega)
admin.site.register(Pedido)
admin.site.register(ProductoDespachado)
admin.site.register(CantidadMaxAceptada)
