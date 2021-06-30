from .models import Lote, Pedido, ProductoBodega, ProductoDespachado
from datetime import datetime

SKU_VACUNAS = ['10001']

TIEMPOS_PRODUCCION = {
    '30013' : 20
}

def factibildad(sku, cantidad_solicitada, fecha_entrega):
    
    if sku not in SKU_VACUNAS:
        # Es un producto normal
        lotes = Lote.objects.filter(
            sku=sku, 
            fecha_vencimiento=fecha_entrega # Acá manejar según tiempo max
        )
        pedidos = Pedido.objects.filter(
            sku=sku,
            fecha_disponible=fecha_entrega, # Acá también manejar
            disponible_para_uso=True
        )

        cantidad_productos_lotes = 0
        for lote in lotes:
            cantidad_productos_lotes += lote.cantidad_disponible


        cantidad_productos_pedidos = 0
        for pedido in pedidos:
            cantidad_productos_pedidos += pedido.cantidad
        
        if cantidad_solicitada <= cantidad_productos_lotes:
            return True # Puedo hacerme cargo de la OC inmediatamente
        elif cantidad_solicitada <= cantidad_productos_lotes + cantidad_productos_pedidos:
            return True
        elif cantidad_solicitada > cantidad_productos_lotes + cantidad_productos_pedidos:
            # Evalúo si alcanzo a producir lo que me falta
            tiempo_prod = TIEMPOS_PRODUCCION[sku]
            delta = 10
            if fecha_entrega > datetime.now() + datetime.min(tiempo_prod + delta):
                return False
            else:
                # 

    else:
        # Es una vacuna y requiere fabricación entre medio
        return False