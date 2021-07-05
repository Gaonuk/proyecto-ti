from .models import Pedido, ProductoBodega, ProductoDespachado
from datetime import datetime
from .warehouse import fabricar_producto

SKU_VACUNAS = ['10001','10002','10005']

TIEMPOS_PRODUCCION_PROPIOS = {
    '108': 25,
    '119': 45,
    '129': 15,
    '121': 30,
    '132': 15,
    '1000': 50,
    '1001': 40,
    '10001': 35,
    '10002': 25,
    '10005': 40,
}


def stock_no_reservado(sku, fecha_vencimiento, margen_tiempo=5):
    all_stock = ProductoBodega.objects.filter(
        sku=sku,
        oc_reservada=None,
    )  
    stock_valido = []
    for producto in all_stock:
        if producto.fecha_vencimiento + margen_tiempo < fecha_vencimiento:
            stock_valido.append(producto)
    return stock_valido

def pedidos_no_reservados(sku, fecha_entrega, margen_tiempo=5):
    pedidos = Pedido.objects.filter(
            sku=sku,
            disponible_para_uso=True
        )
    pedidos_validos = []
    for producto in pedidos:
        if producto.fecha_vencimiento + margen_tiempo < fecha_entrega:
            pedidos_validos.append(producto)
    return pedidos_validos


# Factibilidad
# Reviso el stock en bodega que esté disponible y si tengo del SKU que necesito, lo dejo reservado pero NO lo despacho
# Reviso los pedidos que aún no llegan, y que estén disponibles para uso y también los dejo como no disponibles para que no se consideren para una OC distinta
# Si luego de estas reservas aún me faltan productos, realizo el pedido correspondiente con disponible_para_uso = False


def factibildad(sku, cantidad_solicitada, fecha_entrega, oc_id = None):
    print(f'{datetime.now()}: Análisis de factibilidad\n{sku} - {cantidad_solicitada} - {fecha_entrega}')
    if sku not in TIEMPOS_PRODUCCION_PROPIOS.keys():

        return False
    pedidos = pedidos_no_reservados(sku, fecha_entrega, 15)
    num_productos_pedidos = 0
    for pedido in pedidos:
        num_productos_pedidos += pedido.cantidad
    stock_disponible = stock_no_reservado(sku, fecha_entrega, 10)
    num_productos_stock = len(stock_disponible)

    if sku not in SKU_VACUNAS:
        # Es un producto normal

        total_productos = num_productos_pedidos + num_productos_stock
        
        print(f'Cantidad en almacenes: {num_productos_stock}\nCantidad en camino: {num_productos_pedidos}\nTotal: {total_productos}')

        if cantidad_solicitada <= num_productos_stock:
            # Hay que reservar los productos con la OC correspondiente.
            reservados = 0
            for producto in stock_disponible:
                if reservados == cantidad_solicitada:
                    break
                producto.oc_reservada = oc_id
                reservados += 1

            print(f'Usando stock disponible de SKU {sku}, se reservaron {reservados} de un total de {cantidad_solicitada} para OC {oc_id}.')
            return True 
        elif cantidad_solicitada <= num_productos_pedidos + num_productos_stock:
            # Hay que reservar los productos con la OC correspondiente.
            reservados = 0
            for producto in stock_disponible:
                producto.oc_reservada = oc_id
                reservados += 1
                if reservados == cantidad_solicitada:
                    break
            if reservados:
                print(f'Usando stock disponible de SKU {sku}, se reservaron {reservados} de un total de {cantidad_solicitada} para OC {oc_id}.')
            # Hay que reservar los pedidos
            productos_restantes = cantidad_solicitada - reservados
            pedidos_reservados = 0
            for pedido in pedidos:
                pedido.disponible_para_uso = False
                pedidos_reservados += pedido.cantidad
                productos_restantes -= pedido.cantidad
                if productos_restantes <= 0:
                    break
            if pedidos_reservados:
                print(f'Usando pedidos en camino de SKU {sku}, se reservaron {pedidos_reservados} de un total de {cantidad_solicitada} para OC {oc_id}.')
            print(f'En total se reservaron {pedidos_reservados + reservados} de un total de {cantidad_solicitada} de SKU {sku}.')
            return True

        elif cantidad_solicitada > total_productos:
            # Evalúo si alcanzo a producir lo que me falta
            tiempo_prod = TIEMPOS_PRODUCCION_PROPIOS[sku]
            delta = 10
            if fecha_entrega < datetime.now() + datetime.min(tiempo_prod + delta):
                print(f'No alcanzo a entregar en esa fecha.')
                return False
            else:
                # Hay que reservar los productos con la OC correspondiente.
                reservados = 0
                for producto in stock_disponible:
                    producto.oc_reservada = oc_id
                    reservados += 1
                    if reservados == cantidad_solicitada:
                        break
                print(f'Usando stock disponible de SKU {sku}, se reservaron {reservados} de un total de {cantidad_solicitada} para OC {oc_id}.')
                # Hay que reservar los pedidos
                productos_restantes = cantidad_solicitada - reservados
                pedidos_reservados = 0
                for pedido in pedidos:
                    pedido.disponible_para_uso = False
                    pedidos_reservados += pedido.cantidad
                    productos_restantes -= pedido.cantidad
                    if productos_restantes <= 0:
                        break
                print(f'Usando pedidos en camino de SKU {sku}, se reservaron {pedidos_reservados} de un total de {cantidad_solicitada} para OC {oc_id}.')
                print(f'En total se reservaron {pedidos_reservados + reservados} de un total de {cantidad_solicitada} de SKU {sku}.')
                productos_a_pedir = cantidad_solicitada-pedidos_reservados-reservados
                print(f'Debo pedir {productos_a_pedir} de {sku} para satisfacer la OC.')

                # Hay que hacer un pedido de la diferencia
                
                body_fabricar = {
                    'sku': sku,
                    'cantidad': productos_a_pedir
                }
                response = fabricar_producto(body_fabricar).json()
                pedido = Pedido.objects.get(pk=response['_id'])
                pedido.disponible_para_uso = False
                pedido.save()

                return True

    else:
        # Es una vacuna y requiere fabricación entre medio
        print(f'Este sku {sku} es una vacuna, y aún no está implementado su manejo')
        return False