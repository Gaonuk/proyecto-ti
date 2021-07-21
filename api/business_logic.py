from .models import CantidadMaxAceptada, EmbassyOC, Pedido, ProductoBodega, ProductoDespachado, Log, RecievedOC
from datetime import datetime, timedelta
from .warehouse import fabricar_producto, fabricar_vacuna
from .OC import crear_oc
import random

from .INFO_SKU.info_sku import PRODUCTOS, FORMULA, NUESTRO_SKU
import math

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

def stock_no_reservado(sku):
    all_stock = ProductoBodega.objects.filter(
        sku=str(sku),
        oc_reservada='',
    )  
    return all_stock

def pedidos_no_reservados(sku):
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
        if str(sku) not in NUESTRO_SKU:
            return False
        pedidos = pedidos_no_reservados(sku)
        num_productos_pedidos = 0
        for pedido in pedidos:
            num_productos_pedidos += pedido.cantidad
        stock_disponible = stock_no_reservado(sku)
        num_productos_stock = len(stock_disponible)
        if str(sku) not in SKU_VACUNAS:
            # Revisar si aún puedo aceptar dado el máximo actual de OC para ingredientes
            ordenes_aceptadas = RecievedOC.objects.filter(
                estado="aceptada",
                sku__in=NUESTRO_SKU
            )
            max_vacunas = CantidadMaxAceptada.objects.get(pk='ingredientes')
            if ordenes_aceptadas.count() >= max_vacunas.cantidad:
                log_message += f'Se rechaza la OC por haber alcanzado el máximo permitido de OC de ingredientes aceptadas.'
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

        elif str(sku) in SKU_VACUNAS:
            log_message += f'Este sku {sku} es una vacuna.'
            # Revisar si aún puedo aceptar dado el máximo actual de OC para ingredientes
            ordenes = EmbassyOC.objects.all()
            ordenes_aceptadas = EmbassyOC.objects.filter(
                estado="aceptada"
            )
            ordenes_finalizadas = EmbassyOC.objects.filter(
                estado="finalizada"
            )  

            porcentaje_aceptacion_rechazando = (ordenes_aceptadas.count() + ordenes_finalizadas.count())/ (ordenes.count()+1)
            # Porcentaje en caso de RECHAZAR la OC actual

            if porcentaje_aceptacion_rechazando > 0.85:
                log_message += 'Se rechaza la OC para vacunas. El porcentaje de aceptación actual es: {porcentaje_aceptacion_rechazando*100}%'
                log = Log(mensaje=log_message)
                log.save()
                return False

            # max_vacunas = CantidadMaxAceptada.objects.get(pk='vacunas')
            # if ordenes_aceptadas.count() >= max_vacunas.cantidad:
            #     log_message += f'Se rechaza la OC por haber alcanzado el máximo permitido de OC de vacunas aceptadas.'
            #     log = Log(mensaje=log_message)
            #     log.save()
            #     return False

            sku_vacuna = str(sku)
            tamano_lote_vacuna = int(PRODUCTOS[sku_vacuna]['Lote producción'])
            lotes_vacuna_solicitados = math.ceil(cantidad_solicitada/tamano_lote_vacuna)
            for sku_ingrediente in FORMULA[sku_vacuna]:
                tamano_lote_ingrediente = int(FORMULA[sku_vacuna][sku_ingrediente])
                unidades_ing_necesarias = tamano_lote_ingrediente*lotes_vacuna_solicitados
                if sku_ingrediente in NUESTRO_SKU:
                    body_fabricar = {
                        'sku': str(sku_ingrediente),
                        'cantidad': unidades_ing_necesarias
                    }
                    response = fabricar_producto(body_fabricar).json()
                    pedido = Pedido.objects.get(pk=response['_id'])
                    pedido.disponible_para_uso = False
                    pedido.save()   
                    log_message += f'Se mandó a fabricar {unidades_ing_necesarias} de {sku_ingrediente}.'
                else:
                    
                    
                    # Elijo dos grupos al azar para pedir
                    proveedores = PRODUCTOS[sku_ingrediente]['Grupos Productores']
                    index_1 = random.randint(0, len(proveedores)-1)
                    proveedores.pop(index_1)
                    index_2 = random.randint(0, len(proveedores-1))
                    grupo_proveedor_1 = PRODUCTOS[sku_ingrediente]['Grupos Productores'][index_1]
                    grupo_proveedor_2 = PRODUCTOS[sku_ingrediente]['Grupos Productores'][index_2]


                    # Esta sección es para dosificar las ordenes de compra en caso de que superen las 80 unidades
                    unidades_restantes_por_pedir = unidades_ing_necesarias
                    while unidades_restantes_por_pedir > 0:
                        if unidades_restantes_por_pedir > 80:
                            crear_oc(grupo_proveedor_1, sku_ingrediente, 80)
                            crear_oc(grupo_proveedor_2, sku_ingrediente, 80)
                            unidades_restantes_por_pedir -= 80
                        else:
                            crear_oc(grupo_proveedor_1, sku_ingrediente, unidades_ing_necesarias)
                            crear_oc(grupo_proveedor_2, sku_ingrediente, unidades_ing_necesarias)
                            break
                        
                    log_message += f'Se mandó a pedir {unidades_ing_necesarias} de {sku_ingrediente} tanto al grupo {grupo_proveedor_1} como al grupo {grupo_proveedor_2}.'

            porcentaje_aceptacion_aceptando = (ordenes_aceptadas.count() + ordenes_finalizadas.count()+1)/ (ordenes.count()+1)
            # Es una vacuna y requiere fabricación entre medio
            log_message += f'Se acepta la OC para vacunas. El porcentaje de aceptación actual es: {porcentaje_aceptacion_aceptando*100}%'
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