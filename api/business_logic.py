from .models import Pedido, ProductoBodega, ProductoDespachado, Log
from datetime import datetime, timedelta
from .warehouse import fabricar_producto
import pytz

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

utc = pytz.UTC

def stock_no_reservado(sku, fecha_vencimiento, margen_tiempo=5):
    all_stock = ProductoBodega.objects.filter(
        sku=str(sku),
        oc_reservada='',
    )  
    stock_valido = []
    for producto in all_stock:
        fecha_producto_venc = utc.localize(producto.fecha_vencimiento)
        fecha_producto_venc.replace(tzinfo=utc)
        fecha_venc = utc.localize(fecha_vencimiento)
        fecha_venc.replace(tzinfo=utc)
        if fecha_producto_venc + timedelta(minutes=margen_tiempo) < fecha_venc:
            stock_valido.append(producto)
    return stock_valido

def pedidos_no_reservados(sku, fecha_entrega, margen_tiempo=5):
    # print("A--------------------------------")
    pedidos = Pedido.objects.filter(
            sku=str(sku),
            disponible_para_uso=True
        )
    # print("B--------------------------------")
    pedidos_validos = []
    for producto in pedidos:
        # print("C--------------------------------")
        fecha_disp = utc.localize(producto.fecha_disponible)
        fecha_disp.replace(tzinfo=utc)
        fecha_entr = utc.localize(fecha_entrega)
        fecha_entr.replace(tzinfo=utc)
        if fecha_disp + timedelta(minutes=margen_tiempo) < fecha_entr:
            # print("D--------------------------------")
            pedidos_validos.append(producto)
        # print("E--------------------------------")
    return pedidos_validos


# Factibilidad
# Reviso el stock en bodega que esté disponible y si tengo del SKU que necesito, lo dejo reservado pero NO lo despacho
# Reviso los pedidos que aún no llegan, y que estén disponibles para uso y también los dejo como no disponibles para que no se consideren para una OC distinta
# Si luego de estas reservas aún me faltan productos, realizo el pedido correspondiente con disponible_para_uso = False


def factibildad(sku, cantidad_solicitada, fecha_entrega, oc_id = None):
    #print(f'{datetime.now()}: Análisis de factibilidad\n{sku} - {cantidad_solicitada} - {fecha_entrega}')
    log_inicio = Log(mensaje=f'{datetime.now()}: Análisis de factibilidad {oc_id}\n{sku} - {cantidad_solicitada} - {fecha_entrega}')
    log_inicio.save()
    try: 
        if sku not in TIEMPOS_PRODUCCION_PROPIOS.keys():
            # print("3--------------------------------")
            return False
        # print("2--------------------------------")
        pedidos = pedidos_no_reservados(sku, fecha_entrega, 15)
        # print("1--------------------------------")
        num_productos_pedidos = 0
        # print("4--------------------------------")
        for pedido in pedidos:
            # print("5--------------------------------")
            num_productos_pedidos += pedido.cantidad
        # print("6--------------------------------")
        stock_disponible = stock_no_reservado(sku, fecha_entrega, 10)
        # print("7--------------------------------")
        num_productos_stock = len(stock_disponible)
        # print("8--------------------------------")
        if sku not in SKU_VACUNAS:
            # Es un producto normal
            # print("9--------------------------------")
            total_productos = num_productos_pedidos + num_productos_stock
            
            #print(f'Cantidad en almacenes: {num_productos_stock}\nCantidad en camino: {num_productos_pedidos}\nTotal: {total_productos}')
            log_previo_revisiones = Log(mensaje=f'Factibilidad {oc_id}: Cantidad en almacenes: {num_productos_stock}\nCantidad en camino: {num_productos_pedidos}\nTotal: {total_productos}')
            log_previo_revisiones.save()
            if cantidad_solicitada <= num_productos_stock:
                # Hay que reservar los productos con la OC correspondiente.
                reservados = 0
                for producto in stock_disponible:
                    if reservados == cantidad_solicitada:
                        break
                    producto.oc_reservada = oc_id
                    reservados += 1

                # print(f'Usando stock disponible de SKU {sku}, se reservaron {reservados} de un total de {cantidad_solicitada} para OC {oc_id}.')
                log_stock_alcanza = Log(mensaje=f'Factibilidad {oc_id}: Usando stock disponible de SKU {sku}, se reservaron {reservados} de un total de {cantidad_solicitada} para OC {oc_id}.')
                log_stock_alcanza.save()
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
                    # print(f'Usando stock disponible de SKU {sku}, se reservaron {reservados} de un total de {cantidad_solicitada} para OC {oc_id}.')
                    log_stock_alcanza = Log(mensaje=f'Factibilidad {oc_id}: Usando stock disponible de SKU {sku}, se reservaron {reservados} de un total de {cantidad_solicitada} para OC {oc_id}.')
                    log_stock_alcanza.save()
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
                    # print(f'Usando pedidos en camino de SKU {sku}, se reservaron {pedidos_reservados} de un total de {cantidad_solicitada} para OC {oc_id}.')
                    log_pedidos = Log(mensaje=f'Factibilidad {oc_id}: Usando pedidos en camino de SKU {sku}, se reservaron {pedidos_reservados} de un total de {cantidad_solicitada} para OC {oc_id}.')
                    log_pedidos.save()
                # print(f'En total se reservaron {pedidos_reservados + reservados} de un total de {cantidad_solicitada} de SKU {sku}.')
                log_reservas = Log(mensaje= f'Factibilidad {oc_id}: En total se reservaron {pedidos_reservados + reservados} de un total de {cantidad_solicitada} de SKU {sku}.')
                log_reservas.save()
                return True

            elif cantidad_solicitada > total_productos:
                # Evalúo si alcanzo a producir lo que me falta
                tiempo_prod = TIEMPOS_PRODUCCION_PROPIOS[str(sku)]
                delta = 10
                fecha_ent = utc.localize(fecha_entrega) 
                fecha_ent.replace(tzinfo=utc)
                fecha_ahora = utc.localize(datetime.now())
                fecha_ahora.replace(tzinfo=utc)
                if fecha_ent < fecha_ahora + timedelta(minutes=tiempo_prod + delta):
                    print(f'No alcanzo a entregar en esa fecha.')
                    log_rechazo = Log(mensaje=f'Factibilidad {oc_id}: No alcanzo a entregar en esa fecha. Rechazando OC {oc_id}')
                    log_rechazo.save()
                    return False
                else:
                    # Hay que reservar los productos con la OC correspondiente.
                    reservados = 0
                    for producto in stock_disponible:
                        producto.oc_reservada = oc_id
                        reservados += 1
                        if reservados == cantidad_solicitada:
                            break
                    # print(f'Usando stock disponible de SKU {sku}, se reservaron {reservados} de un total de {cantidad_solicitada} para OC {oc_id}.')
                    log_stock_alcanza = Log(mensaje=f'Factibilidad {oc_id}: Usando stock disponible de SKU {sku}, se reservaron {reservados} de un total de {cantidad_solicitada} para OC {oc_id}.')
                    log_stock_alcanza.save()
                    # Hay que reservar los pedidos
                    productos_restantes = cantidad_solicitada - reservados
                    pedidos_reservados = 0
                    for pedido in pedidos:
                        pedido.disponible_para_uso = False
                        pedidos_reservados += pedido.cantidad
                        productos_restantes -= pedido.cantidad
                        if productos_restantes <= 0:
                            break
                    # print(f'Factibilidad {oc_id}: Usando pedidos en camino de SKU {sku}, se reservaron {pedidos_reservados} de un total de {cantidad_solicitada} para OC {oc_id}.')
                    log_pedidos_existentes = Log(mensaje= f'Factibilidad {oc_id}: Usando pedidos en camino de SKU {sku}, se reservaron {pedidos_reservados} de un total de {cantidad_solicitada} para OC {oc_id}.')
                    log_pedidos_existentes.save()
                    # print(f'Factibilidad {oc_id}: En total se reservaron {pedidos_reservados + reservados} de un total de {cantidad_solicitada} de SKU {sku}.')
                    productos_a_pedir = cantidad_solicitada-pedidos_reservados-reservados
                    print(f'Factibilidad {oc_id}: Debo pedir {productos_a_pedir} de {sku} para satisfacer la OC.')
                    log_pedidos_nuevos = Log(mensaje = f'Factibilidad {oc_id}: Debo pedir {productos_a_pedir} de {sku} para satisfacer la OC.')

                    # Hay que hacer un pedido de la diferencia
                    
                    body_fabricar = {
                        'sku': str(sku),
                        'cantidad': productos_a_pedir
                    }
                    print("ADAASAAS")
                    response = fabricar_producto(body_fabricar).json()
                    print("JDISJIDSJIDS")
                    pedido = Pedido.objects.get(pk=response['_id'])
                    print("DMSJDMSJDS")
                    pedido.disponible_para_uso = False
                    pedido.save()


                    return True

        else:
            # Es una vacuna y requiere fabricación entre medio
            print(f'Este sku {sku} es una vacuna, y aún no está implementado su manejo')
            log_vacuna = Log(mensaje=f'Factibilidad {oc_id}: Este sku {sku} es una vacuna, y aún no está implementado su manejo')
            log_vacuna.save()
            return False
    except Exception as err:
        log = Log(mensaje='Error en Factibilidad {oc_id}: '+str(err)+'\nSe rechazó la OC')
        log.save()
        return False