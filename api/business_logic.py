from .models import CantidadMaxAceptada, Pedido, ProductoBodega, ProductoDespachado, Log, RecievedOC
from datetime import datetime, timedelta
from .warehouse import fabricar_producto

SKU_VACUNAS = ['10001','10002','10003','10004','10005','10006']

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
        sku=str(sku),
        oc_reservada='',
    )  
    return all_stock

def pedidos_no_reservados(sku, fecha_entrega, margen_tiempo=5):
    pedidos = Pedido.objects.filter(
            sku=str(sku),
            disponible_para_uso=True
        )
    return pedidos


# Factibilidad
# Reviso el stock en bodega que esté disponible y si tengo del SKU que necesito, lo dejo reservado pero NO lo despacho
# Reviso los pedidos que aún no llegan, y que estén disponibles para uso y también los dejo como no disponibles para que no se consideren para una OC distinta
# Si luego de estas reservas aún me faltan productos, realizo el pedido correspondiente con disponible_para_uso = False


def factibildad(sku, cantidad_solicitada, fecha_entrega, oc_id = None):
    #print(f'{datetime.now()}: Análisis de factibilidad\n{sku} - {cantidad_solicitada} - {fecha_entrega}')
    log_message = f'Factibilidad | OC {oc_id} | SKU {sku} | # {cantidad_solicitada} | Deadline {fecha_entrega}\n' 
    try:
        if str(sku) not in TIEMPOS_PRODUCCION_PROPIOS.keys():
            return False
        pedidos = pedidos_no_reservados(sku, fecha_entrega, 15)
        num_productos_pedidos = 0
        for pedido in pedidos:
            num_productos_pedidos += pedido.cantidad
        stock_disponible = stock_no_reservado(sku, fecha_entrega, 10)
        num_productos_stock = len(stock_disponible)
        if str(sku) not in SKU_VACUNAS:
            # Revisar si aún puedo aceptar dado el máximo actual de OC para ingredientes
            ordenes_aceptadas = RecievedOC.objects.filter(
                estado="aceptada",
                sku__in=TIEMPOS_PRODUCCION_PROPIOS.keys()
            )
            max_vacunas = CantidadMaxAceptada.objects.get(pk='ingredientes')
            if ordenes_aceptadas.count() >= max_vacunas:
                log_message += Log(mensaje=f'Se rechaza la OC por haber alcanzado el máximo permitido de OC de ingredientes aceptadas.')
                log = Log(mensaje=log_message)
                log.save()
                return False

            # Es un producto normal
            total_productos = num_productos_pedidos + num_productos_stock
            log_message += f'Cantidad en almacenes: {num_productos_stock}\nCantidad en camino: {num_productos_pedidos}\nTotal: {total_productos}\n'
            if cantidad_solicitada <= num_productos_stock:
                # Hay que reservar los productos con la OC correspondiente.
                reservados = 0
                for producto in stock_disponible:
                    if reservados == cantidad_solicitada:
                        break
                    producto.oc_reservada = oc_id
                    reservados += 1

                log_message += f'Usando stock disponible de SKU {sku}, se reservaron {reservados} de un total de {cantidad_solicitada} para OC {oc_id}.\n'

                body_fabricar = {
                        'sku': str(sku),
                        'cantidad': reservados
                    }
                response = fabricar_producto(body_fabricar).json()
                pedido = Pedido.objects.get(pk=response['_id'])
                pedido.disponible_para_uso = True
                pedido.save()

                log_message += f'Se enviaron a fabricar {reservados} SKU {sku}.\n'
                log = Log(mensaje=log_message)
                log.save()
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
                    log_stock_alcanza = Log(mensaje=f'Usando stock disponible de SKU {sku}, se reservaron {reservados} de un total de {cantidad_solicitada} para OC {oc_id}.')
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
                    log_message += f'Usando pedidos en camino de SKU {sku}, se reservaron {pedidos_reservados} de un total de {cantidad_solicitada} para OC {oc_id}.\n'
                log_message += f'En total se reservaron {pedidos_reservados + reservados} de un total de {cantidad_solicitada} de SKU {sku}.\n'

                body_fabricar = {
                        'sku': str(sku),
                        'cantidad': pedidos_reservados + reservados
                    }
                response = fabricar_producto(body_fabricar).json()
                pedido = Pedido.objects.get(pk=response['_id'])
                pedido.disponible_para_uso = True
                pedido.save()
                
                log_message += f'Se enviaron a fabricar {pedidos_reservados + reservados} SKU {sku}.\n'
                log = Log(mensaje=log_message)
                log.save()
                return True

            elif cantidad_solicitada > total_productos:
                # Evalúo si alcanzo a producir lo que me falta
                tiempo_prod = TIEMPOS_PRODUCCION_PROPIOS[str(sku)]
                delta = 10
                # fecha_ent = utc.normalize(fecha_entrega).astimezone(utc)
                # # fecha_ent.replace(tzinfo=utc)
                # fecha_ahora = utc.normalize(datetime.now()).astimezone(utc)
                # # fecha_ahora.replace(tzinfo=utc)

                # Este IF nunca ocurrirá
                if False:
                    log_message += f'No alcanzo a entregar en esa fecha. Rechazando OC {oc_id}\n'
                    log_rechazo.save()
                    return False
                elif True:
                    # Hay que reservar los productos con la OC correspondiente.
                    reservados = 0
                    for producto in stock_disponible:
                        producto.oc_reservada = oc_id
                        reservados += 1
                        if reservados == cantidad_solicitada:
                            break
                    log_message += f'Usando stock disponible de SKU {sku}, se reservaron {reservados} de un total de {cantidad_solicitada} para OC {oc_id}.\n'
                    # Hay que reservar los pedidos
                    productos_restantes = cantidad_solicitada - reservados
                    pedidos_reservados = 0
                    for pedido in pedidos:
                        pedido.disponible_para_uso = False
                        pedidos_reservados += pedido.cantidad
                        productos_restantes -= pedido.cantidad
                        if productos_restantes <= 0:
                            break
                    log_message += f'Usando pedidos en camino de SKU {sku}, se reservaron {pedidos_reservados} de un total de {cantidad_solicitada} para OC {oc_id}.\n'
                    productos_a_pedir = cantidad_solicitada-pedidos_reservados-reservados
                    log_message += f'Debo pedir {productos_a_pedir} de {sku} para satisfacer la OC.\n'

                    # Hay que hacer un pedido de la diferencia
                    
                    body_fabricar = {
                        'sku': str(sku),
                        'cantidad': cantidad_solicitada
                    }
                    response = fabricar_producto(body_fabricar).json()
                    pedido = Pedido.objects.get(pk=response['_id'])
                    pedido.disponible_para_uso = False
                    pedido.save()

                    log_message +=  f'Se enviaron a fabricar {cantidad_solicitada} SKU {sku}.\n'
                    log = Log(mensaje=log_message)
                    log.save()      
                    return True

        elif str(sku) in SKU_VACUNAS.keys():
            log_message += Log(mensaje=f'Este sku {sku} es una vacuna.')
            # Revisar si aún puedo aceptar dado el máximo actual de OC para ingredientes
            ordenes_aceptadas = RecievedOC.objects.filter(
                estado="aceptada",
                sku__in=SKU_VACUNAS
            )
            max_vacunas = CantidadMaxAceptada.objects.get(pk='vacunas')
            if ordenes_aceptadas.count() >= max_vacunas:
                log_message += Log(mensaje=f'Se rechaza la OC por haber alcanzado el máximo permitido de OC de vacunas aceptadas.')
                log = Log(mensaje=log_message)
                log.save()
                return False

            # Es una vacuna y requiere fabricación entre medio
            log_message += Log(mensaje=f'Al ser una OC para vacunas y no exceder el máximo permitido, se acepta.')
            log = Log(mensaje=log_message)
            log.save()
            return True
        
        else:
            return False
    except Exception as err:
        log_message += f'Error en Factibilidad {oc_id}: '+str(err)+'\nSe rechazó la OC\n'
        log = Log(mensaje=log_message)
        log.save()
        return False