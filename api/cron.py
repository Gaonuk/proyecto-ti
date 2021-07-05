# Create your tasks here
from .warehouse import despachar_producto, mover_entre_almacenes, mover_entre_bodegas, obtener_almacenes, obtener_productos_almacen, obtener_stock, fabricar_producto
from .models import Log, Pedido, ProductoBodega
import time
from .OC import parse_js_date

def mover_recepcion_a_alm_central():
    almacen_recepcion= None
    almacen_central = None
    almancen_pulmon = None
    almancen_despacho = None
    almacenes = obtener_almacenes().json()
    for almacen in almacenes:
        if almacen['recepcion']:
            almacen_recepcion = almacen
        elif almacen['pulmon']:
            almancen_pulmon = almacen
        elif almacen['despacho']:
            almacen_despacho = almacen
        else:
            almacen_central = almacen

    params = {'almacenId': almacen_recepcion['_id']}
    stock_alm_recepción = obtener_stock(params).json()
    IDs_por_sku_alm_recepcion = {}
    try:
        if len(stock_alm_recepción) > 0:
            if int(almacen_central['totalSpace']) > int(almacen_central['usedSpace']):
                print('Moviendo productos al almacen central...')
                mensaje=''
                for sku in stock_alm_recepción:
                    IDs_por_sku_alm_recepcion[sku['_id']]= []
                    productos_almacen_recepcion = obtener_productos_almacen(
                        {"almacenId": almacen_recepcion['_id'], "sku": sku["_id"]}).json()
                    for producto_almacen in productos_almacen_recepcion:
                        IDs_por_sku_alm_recepcion[sku['_id']].append(producto_almacen['_id'])
                        ############### Instancia productoBodega
                        ###Chequear antes si ya existe por caso que no pueda moverlo al primer intento y ya se haya creado
                        if ProductoBodega.objects.filter(id=producto_almacen['_id']).exists():
                            pass   ## listos
                        else:  ### Bajar cantidad en pedido, borrar si llega a 0, crear productoBodega
                            pedido = Pedido.objects.filter(sku=sku["_id"]).order_by('fecha_disponible').first()
                            id_pedido = pedido.id
                            if pedido.cantidad == 1:
                                pedido.delete()
                                log_pedido = Log(mensaje=f"Se borró el pedido {id_pedido}")
                                log_pedido.save()
                            else:
                                pedido.cantidad -= 1
                            producto_bodega = ProductoBodega(id = producto_almacen['_id'], sku=producto_almacen["sku"], almacen=almacen_recepcion['_id'],\
                                fecha_vencimiento=parse_js_date(producto_almacen["vencimiento"]))
                            log_producto = Log(mensaje=f"Llegó un producto del pedido {id_pedido} y se creó en bodega con id {producto_almacen['_id']}")
                            log_producto.save()
                            producto_bodega.save()
                            pedido.save()
                        #################
                for SKU in IDs_por_sku_alm_recepcion:
                    print(f'Moviendo productos de SKU {SKU}')
                    contador=0
                    for ID_producto in IDs_por_sku_alm_recepcion[SKU]:
                        time.sleep(1)
                        mover_entre_almacenes(
                                {'productoId': ID_producto, "almacenId": almacen_central['_id']})
                        contador+=1
                    mensaje+= f'Se han movido {contador} productos del SKU {SKU} al almacén central\n'
                print(mensaje)
                log_1 = Log(mensaje=mensaje)
                log_1.save()
            else:
                print('El almacen central está lleno')
                log_2 = Log(mensaje='El almacen central está lleno')
                log_2.save()
        else:
            print('No hay productos para mover desde el almacén de recepción')
    except Exception as err:
            log_3 = Log(mensaje=err)
            log_3.save()

def mover_pulmon_a_alm_recepcion():
    almacen_recepcion= None
    almacen_central = None
    almancen_pulmon = None
    almancen_despacho = None
    almacenes = obtener_almacenes().json()
    for almacen in almacenes:
        if almacen['recepcion']:
            almacen_recepcion = almacen
        elif almacen['pulmon']:
            almancen_pulmon = almacen
        elif almacen['despacho']:
            almacen_despacho = almacen
        else:
            almacen_central = almacen

    params = {'almacenId': almancen_pulmon['_id']}
    stock_alm_pulmon = obtener_stock(params).json()
    IDs_por_sku_alm_pulmon = {}
    try:
        if len(stock_alm_pulmon) > 0:
            if int(almacen_recepcion['totalSpace']) > int(almacen_recepcion['usedSpace']):
                print('Moviendo productos al almacen de despacho...')
                mensaje=''
                for sku in stock_alm_pulmon:
                    IDs_por_sku_alm_pulmon[sku['_id']]= []
                    productos_almacen_pulmon = obtener_productos_almacen(
                        {"almacenId": almancen_pulmon['_id'], "sku": sku["_id"]}).json()
                    for producto_almacen in productos_almacen_pulmon:
                        IDs_por_sku_alm_pulmon[sku['_id']].append(producto_almacen['_id'])
                        ############### Instancia productoBodega
                        ###Chequear antes si ya existe por caso que no pueda moverlo al primer intento y se haya creado
                        if ProductoBodega.objects.filter(id=producto_almacen['_id']).exists():
                            pass   ## listos
                        else:  ### Bajar cantidad en pedido, borrar si llega a 0, crear productoBodega
                            pedido = Pedido.objects.filter(sku=sku["_id"]).order_by('fecha_disponible').first()
                            id_pedido = pedido.id
                            if pedido.cantidad == 1:
                                pedido.delete()
                                log_pedido = Log(mensaje=f"Se borró el pedido {id_pedido}")
                                log_pedido.save()
                            else:
                                pedido.cantidad -= 1
                            producto_bodega = ProductoBodega(id = producto_almacen['_id'], sku=producto_almacen["sku"], almacen=almancen_pulmon['_id'],\
                                fecha_vencimiento=parse_js_date(producto_almacen["vencimiento"]))
                            producto_bodega.save()
                            pedido.save()
                            log_producto = Log(mensaje=f"Llegó un producto del pedido {id_pedido} y se creó en bodega con id {producto_almacen['_id']}")
                            log_producto.save()
                        #################
                        
                for SKU in IDs_por_sku_alm_pulmon:
                    print(f'Moviendo productos de SKU {SKU}')
                    contador=0
                    for ID_producto in IDs_por_sku_alm_pulmon[SKU]:
                        time.sleep(1)
                        mover_entre_almacenes(
                                {'productoId': ID_producto, "almacenId": almacen_recepcion['_id']})
                        contador+=1
                    mensaje+= f'Se han movido {contador} productos del SKU {SKU} al almacén de recepción\n'
                print(mensaje)
                log_1 = Log(mensaje=mensaje)
                log_1.save()
            else:
                print('El almacen de recepción está lleno')
                log_2 = Log(mensaje='El almacen de recepción está lleno')
                log_2.save()
        else:
            print('No hay productos para mover desde el almacén de recepción')

    except Exception as err:
        log_3 = Log(mensaje=err)
        log_3.save()
