from .models import Lote, Pedido, ProductoBodega, ProductoDespachado
from datetime import datetime
from .warehouse import fabricar_producto

SKU_VACUNAS = ['10001']

TIEMPOS_PRODUCCION = {
    '30013' : 20
}

def factibildad(sku, cantidad_solicitada, fecha_entrega):
    print(f'{datetime.now()}: Análisis de factibilidad\n{sku} - {cantidad_solicitada} - {fecha_entrega}')
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
        
        cantidad_productos_total = cantidad_productos_lotes + cantidad_productos_pedidos
        
        print(f'Cantidad en almacenes: {cantidad_productos_lotes}\nCantidad en camino: {cantidad_productos_pedidos}\nTotal: {cantidad_productos_total}')

        if cantidad_solicitada <= cantidad_productos_lotes:
            print(f'Usando solo stock en camino puedo satisfacer el pedido.')
            return True # Puedo hacerme cargo de la OC inmediatamente
        elif cantidad_solicitada <= cantidad_productos_total:
            print(f'Usando stock + pedidos en camino puedo satisfacer el pedido.')
            # Hay que reservar los productos con la OC correspondiente.
            return True
        elif cantidad_solicitada > cantidad_productos_total:
            # Evalúo si alcanzo a producir lo que me falta
            tiempo_prod = TIEMPOS_PRODUCCION[sku]
            delta = 10
            if fecha_entrega < datetime.now() + datetime.min(tiempo_prod + delta):
                print(f'No alcanzo a entregar en esa fecha, porque no me llegan los pedidos.')
                return False
            else:
                # Si me alcanza el tiempo debo pedir más 
                print(f'Debo pedir {cantidad_productos_total-cantidad_solicitada} de {sku} para satisfacer la OC.')
                return True

    else:
        # Es una vacuna y requiere fabricación entre medio
        print(f'Este sku {sku} es una vacuna, y aún no está implementado su manejo')
        return False