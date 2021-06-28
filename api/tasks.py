# Create your tasks here

from celery import shared_task
from django.db.models import aggregates
from .models import AlgunModelo
from celery.utils.log import get_task_logger
import uuid
import random
from .warehouse import despachar_producto, mover_entre_almacenes, mover_entre_bodegas, obtener_almacenes, obtener_productos_almacen, obtener_stock, fabricar_producto
import time
logger = get_task_logger(__name__)

@shared_task
def add(x, y):
    return x + y


@shared_task
def mul(x, y):
    return x * y


@shared_task
def xsum(numbers):
    return sum(numbers)



@shared_task
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

