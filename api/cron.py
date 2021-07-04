# Create your tasks here
from api.models import RecievedOC, ProductoBodega
from .warehouse import despachar_producto, mover_entre_almacenes, mover_entre_bodegas, obtener_almacenes, obtener_productos_almacen, obtener_stock, fabricar_producto
import time
# import kronos
import os
from .arrays_clients_ids_oc import IDS_DEV, IDS_PROD
from .arrays_almacenes_recep import RECEPCIONES_DEV, RECEPCIONES_PROD

if os.environ.get('DJANGO_DEVELOPMENT'):
    ids_grupos = IDS_DEV
    ids_recepcion = RECEPCIONES_DEV
else:
    ids_grupos = IDS_PROD
    ids_recepcion = RECEPCIONES_PROD

# @kronos.register('*/2 * * * *')
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
            for SKU in IDs_por_sku_alm_recepcion:
                print(f'Moviendo productos de SKU {SKU}')
                for ID_producto in IDs_por_sku_alm_recepcion[SKU]:
                    time.sleep(1)
                    mover_entre_almacenes(
                            {'productoId': ID_producto, "almacenId": almacen_central['_id']})
                mensaje+= f'Se han movido {len(IDs_por_sku_alm_recepcion[SKU])} productos del SKU {SKU} al almacén central\n'
            print(mensaje)
        else:
            print('El almacen central está lleno')
    else:
        print('No hay productos para mover desde el almacén de recepción')

def revision_oc():
    not_completed_oc = RecievedOC.objects.filter(estado="aceptada")
    for orden in not_completed_oc:
        orden.cantidad_despachada = ProductoBodega.objects.filter(oc_reservada=orden.id).count()
        orden.save()
        sku = orden.sku
        cantidad = orden.cantidad - orden.cantidad_despachada
        if cantidad > 0:
            productos_disponibles = ProductoBodega.objects.filter(sku=sku, oc_reservada=None)
            cantidad_disponible = productos_disponibles.count()
            if cantidad_disponible <= cantidad:
                for producto in productos_disponibles:
                    producto.oc_reservada = orden.id
                    producto.save()
                orden.cantidad_despachada = ProductoBodega.objects.filter(oc_reservada=orden.id).count()
            else:
                contador = 0
                for producto in productos_disponibles:
                    producto.oc_reservada = orden.id
                    producto.save()
                    contador += 1
                    if contador == cantidad:
                        break
        if orden.cantidad_despachada >= orden.cantidad:
            orden.estado = "finalizada"
        orden.save()

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
    productos_despacho = ProductoBodega.objects.filter(oc_reservada__isnull=False, almacen__in=ids_almacen)
    for producto in productos_despacho:
        if producto.almacen != almacen_pulmon['_id']:
            try:
                mover_entre_almacenes({'productoId': producto.id, "almacenId": almacen_despacho['_id']})
                print(f'Se han movido 1 producto del SKU {producto.sku} al almacén desapcho\n')
                time.sleep(1)
            except:
                print(f'Alamacen Despacho se encuentra lleno')
        else:
            try:
                mover_entre_almacenes({'productoId': producto.id, "almacenId": almacen_recepcion['_id']})
                print(f'Se han movido 1 producto del SKU {producto.sku} al almacén recepción\n')
                time.sleep(1)
                try:
                    mover_entre_almacenes({'productoId': producto.id, "almacenId": almacen_despacho['_id']})
                    print(f'Se han movido 1 producto del SKU {producto.sku} al almacén desapcho\n')
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
    productos_para_despachar = ProductoBodega.objects.filter(oc_reservada__isnull=False, almacen__in=almacen_despacho['_id'])
    for producto in productos_para_despachar:
        oc = producto.oc_reservada
        oc_object = RecievedOC.objects.filter(id=oc)
        posicion = ids_grupos.index(oc.cliente)
        almacen_id = ids_recepcion[posicion]
        respuesta = mover_entre_bodegas({'productoId': producto.id, 'almacenId': almacen_id, 'oc': oc, 'precio': oc_object.precio_unitario}).json()
        try:
            print(respuesta["error"])
        except:
            print(f"El producto de id {producto.id} fue despachado al almacen {almacen_id}")
        time.sleep(1)




