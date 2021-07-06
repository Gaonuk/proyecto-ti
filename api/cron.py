# Create your tasks here
from api.models import RecievedOC, ProductoBodega
from .warehouse import despachar_producto, mover_entre_almacenes, mover_entre_bodegas, obtener_almacenes, obtener_productos_almacen, obtener_stock, fabricar_producto
from .models import Log, Pedido, ProductoBodega
import time

from .OC import parse_js_date
import os
from .arrays_clients_ids_oc import IDS_DEV, IDS_PROD
from .arrays_almacenes_recep import RECEPCIONES_DEV, RECEPCIONES_PROD

if os.environ.get('DJANGO_DEVELOPMENT')=='true':
    ids_grupos = IDS_DEV
    ids_recepcion = RECEPCIONES_DEV
else:
    ids_grupos = IDS_PROD
    ids_recepcion = RECEPCIONES_PROD

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
            almacen_pulmon = almacen
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
                        try:
                            if ProductoBodega.objects.filter(id=producto_almacen['_id']).exists():
                                pass   ## listos
                            else:  ### Bajar cantidad en pedido, borrar si llega a 0, crear productoBodega
                                pedido = Pedido.objects.filter(sku=str(sku["_id"])).order_by('fecha_disponible').first()
                                id_pedido = pedido.id
                                if pedido.cantidad == 1:
                                    pedido.delete()
                                    log_pedido = Log(mensaje=f"Recepción a Central: Se borró el pedido {id_pedido}")
                                    log_pedido.save()
                                else:
                                    pedido.cantidad -= 1
                                producto_bodega = ProductoBodega(id = producto_almacen['_id'], sku=str(producto_almacen["sku"]), almacen=almacen_recepcion['_id'],\
                                    fecha_vencimiento=parse_js_date(producto_almacen["vencimiento"]))
                                log_producto = Log(mensaje=f"Recepción a Central: Llegó un producto del pedido {id_pedido} y se creó en bodega con id {producto_almacen['_id']}")
                                log_producto.save()
                                producto_bodega.save()
                                pedido.save()
                        except:
                            pass
                        #################
                for SKU in IDs_por_sku_alm_recepcion:
                    print(f'Moviendo productos de SKU {SKU}')
                    contador=0
                    for ID_producto in IDs_por_sku_alm_recepcion[SKU]:
                        time.sleep(1)
                        mover_entre_almacenes(
                                {'productoId': ID_producto, "almacenId": almacen_central['_id']})
                        contador+=1
                    mensaje+= f'Recepción a Central: Se han movido {contador} productos del SKU {SKU} al almacén central\n'
                print(mensaje)
                log_1 = Log(mensaje=mensaje)
                log_1.save()
            else:
                print('El almacen central está lleno')
                log_2 = Log(mensaje='Recepción a Central: El almacen central está lleno')
                log_2.save()
        else:
            print('No hay productos para mover desde el almacén de recepción')
    except Exception as err:
            log_3 = Log(mensaje='Recepción a Central: '+err)
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
                        try:
                            if ProductoBodega.objects.filter(id=producto_almacen['_id']).exists():
                                pass   ## listos
                            else:  ### Bajar cantidad en pedido, borrar si llega a 0, crear productoBodega
                                pedido = Pedido.objects.filter(sku=str(sku["_id"])).order_by('fecha_disponible').first()
                                id_pedido = pedido.id
                                if pedido.cantidad == 1:
                                    pedido.delete()
                                    log_pedido = Log(mensaje=f"Pulmón a Recepción: Se borró el pedido {id_pedido}")
                                    log_pedido.save()
                                else:
                                    pedido.cantidad -= 1
                                producto_bodega = ProductoBodega(id = producto_almacen['_id'], sku=str(producto_almacen["sku"]), almacen=almancen_pulmon['_id'],\
                                    fecha_vencimiento=parse_js_date(producto_almacen["vencimiento"]))
                                producto_bodega.save()
                                pedido.save()
                                log_producto = Log(mensaje=f"Pulmón a Recepción: Llegó un producto del pedido {id_pedido} y se creó en bodega con id {producto_almacen['_id']}")
                                log_producto.save()
                        except:
                            pass
                        #################
                        
                for SKU in IDs_por_sku_alm_pulmon:
                    print(f'Moviendo productos de SKU {SKU}')
                    contador=0
                    for ID_producto in IDs_por_sku_alm_pulmon[SKU]:
                        time.sleep(1)
                        mover_entre_almacenes(
                                {'productoId': ID_producto, "almacenId": almacen_recepcion['_id']})
                        contador+=1
                    mensaje+= f'Pulmón a Recepción: Se han movido {contador} productos del SKU {SKU} al almacén de recepción\n'
                print(mensaje)
                log_1 = Log(mensaje=mensaje)
                log_1.save()
            else:
                print('El almacen de recepción está lleno')
                log_2 = Log(mensaje='Pulmón a Recepción: El almacen de recepción está lleno')
                log_2.save()
        else:
            print('No hay productos para mover desde el almacén de recepción')
    except Exception as err:
        log_3 = Log(mensaje='Pulmón a Recepción: '+err)
        log_3.save()

def revision_oc():
    not_completed_oc = RecievedOC.objects.filter(estado="aceptada")
    for orden in not_completed_oc:
        print(f"Actualizando OC de id {orden.id}")
        orden.cantidad_despachada = ProductoBodega.objects.filter(oc_reservada=orden.id).count()
        orden.save()
        sku = orden.sku
        cantidad = orden.cantidad - orden.cantidad_despachada
        if cantidad > 0:
            productos_disponibles = ProductoBodega.objects.filter(sku=str(sku), oc_reservada='')
            cantidad_disponible = productos_disponibles.count()
            if cantidad_disponible <= cantidad:
                for producto in productos_disponibles:
                    producto.oc_reservada = orden.id
                    producto.save()
                    print(f"Asignando producto de id {producto.id} a OC de id {orden.id}")
                    log = Log(mensaje=f"Revision OC: Asignando producto de id {producto.id} a OC de id {orden.id}")
                    log.save()
                orden.cantidad_despachada = ProductoBodega.objects.filter(oc_reservada=orden.id).count()
            else:
                contador = 0
                for producto in productos_disponibles:
                    producto.oc_reservada = orden.id
                    producto.save()
                    log = Log(mensaje=f"Revision OC: Asignando producto de id {producto.id} a OC de id {orden.id}")
                    log.save()
                    print(f"Asignando producto de id {producto.id} a OC de id {orden.id}")
                    contador += 1
                    if contador == cantidad:
                        break
        if orden.cantidad_despachada >= orden.cantidad:
            orden.estado = "finalizada"
        orden.save()
        print(f"OC de id {orden.id} actualizada")

def mover_despacho():
    almacenes = obtener_almacenes().json()
    for almacen in almacenes:
        if almacen['recepcion']:
            almacen_recepcion = almacen
        elif almacen['pulmon']:
            almacen_pulmon = almacen
        elif almacen['despacho']:
            almacen_despacho = almacen
        else:
            almacen_central = almacen
    ids_almacen = [almacen_recepcion['_id'], almacen_central['_id'], almacen_pulmon['_id']]
    productos_despacho = ProductoBodega.objects.filter(almacen__in=ids_almacen).exclude(oc_reservada='')
    for producto in productos_despacho:
        if producto.almacen != almacen_pulmon['_id']:
            try:
                mover_entre_almacenes({'productoId': producto.id, "almacenId": almacen_despacho['_id']})
                print(f'Se han movido 1 producto del SKU {producto.sku} al almacén desapcho\n')
                log = Log(mensaje=f'Mover despacho: Se han movido 1 producto del SKU {producto.sku} al almacén despacho\n')
                log.save()
                time.sleep(1)
            except:
                print(f'Alamacen Despacho se encuentra lleno')
        else:
            try:
                mover_entre_almacenes({'productoId': producto.id, "almacenId": almacen_recepcion['_id']})
                print(f'Se han movido 1 producto del SKU {producto.sku} al almacén recepción\n')
                log = Log(mensaje=f'Mover despacho: Se han movido 1 producto del SKU {producto.sku} al almacén recepción\n')
                log.save()
                time.sleep(1)
                try:
                    mover_entre_almacenes({'productoId': producto.id, "almacenId": almacen_despacho['_id']})
                    print(f'Se han movido 1 producto del SKU {producto.sku} al almacén despacho\n')
                    log = Log(mensaje=f'Mover despacho: Se han movido 1 producto del SKU {producto.sku} al almacén despacho\n')
                    log.save()
                    time.sleep(1)
                except:
                    print(f'Alamacen Despacho se encuentra lleno')
            except:
                print(f'Alamcen Recepción se encuentra lleno')


def despachar():
    almacenes = obtener_almacenes().json()
    for almacen in almacenes:
        if almacen['despacho']:
            almacen_despacho = almacen
    try:
        productos_para_despachar = ProductoBodega.objects.filter(almacen=almacen_despacho['_id']).exclude(oc_reservada='')
        print(productos_para_despachar)
        for producto in productos_para_despachar:
            print('despachando...')
            oc = producto.oc_reservada
            oc_object = RecievedOC.objects.filter(id=oc)
            posicion = ids_grupos.index(oc_object[0].cliente)
            almacen_id = ids_recepcion[posicion]
            respuesta = mover_entre_bodegas({'productoId': producto.id, 'almacenId': almacen_id, 'oc': oc, 'precio': oc_object[0].precio_unitario}).json()
            try:
                print(f"Despachar: El producto de id {producto.id} fue despachado al almacen {almacen_id}")
                log = Log(mensaje=f"El producto de id {producto.id} fue despachado al almacen {almacen_id}")
                log.save()
            except:
                print(respuesta["error"])
                log = Log(mensaje=respuesta["error"])
                log.save()

            time.sleep(1)
    except Exception as err:
        log = Log(mensaje='Despachar: '+str(err))
        log.save()

