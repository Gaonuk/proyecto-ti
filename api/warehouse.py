from rest_framework.parsers import JSONParser
from rest_framework import status
import requests
from hashlib import sha1
import hmac
import base64
from .models import Log, Pedido, ProductoBodega, ProductoDespachado
from .OC import parse_js_date, crear_oc
from .INFO_SKU.info_sku import PRODUCTOS, FORMULA, NUESTRO_SKU
import time
from datetime import date, datetime, timedelta
import math
from random import randint, random, uniform
from .arrays_clients_ids_oc import IDS_DEV, IDS_PROD

# Only to define .env variables
import os
import environ
from pathlib import Path
import pytz

utc=pytz.UTC

# BASE DIRECTORY
BASE_DIR = Path(__file__).resolve().parent.parent

SKU_LOTE = {
    '100': 5,
    '104': 6,
    '107': 7,
    '108': 18,
    '109': 2,
    '111': 18,
    '112': 5,
    '113': 12,
    '114': 14,
    '116': 10,
    '117': 20,
    '118': 4,
    '119': 14,
    '128': 3,
    '129': 10,
    '115': 20,
    '120': 5,
    '121': 3,
    '122': 10,
    '124': 5,
    '125': 4,
    '126': 10,
    '127': 5,
    '132': 14,
    '110': 6,
    '103': 9,
    '102': 8,
    '1000': 8,
    '1001': 5,
    '1002': 3,
    '1003': 5,
    '10001': 6,
    '10002': 8,
    '10005': 4,
    '10003': 5,
    '10004': 5,
    '10006': 9,

}

# Initialise environment variables
env = environ.Env()
environ.Env.read_env(env_file=os.path.join(BASE_DIR, 'proyecto13/.env'))


if os.environ.get('DJANGO_DEVELOPMENT') == 'true':
    print('estas en dev')
    cliente = '60bd2a763f1b6100049f1453'
    api_url = env('API_BODEGA_DEV')
    clave_privada = env('CLAVE_BODEGA_DEV')
    ids_oc = IDS_DEV
    url_notif = ''
else:
    print('estas en prod')
    cliente = '60caa3af31df040004e88df0'
    api_url = env('API_BODEGA_PROD')
    clave_privada = env('CLAVE_BODEGA_PROD')
    ids_oc = IDS_PROD
    url_notif = 'http://aysen13.ing.puc.cl/ordenes-compra/{_id}'


def hash_maker(msg: str):
    # función para hacer el hash para el header de Authorization
    hashed_string = hmac.new(
        bytes(clave_privada, 'utf-8'), bytes(msg, 'utf-8'), sha1)
    return base64.b64encode(hashed_string.digest()).decode()


# Funciones auxiliares para interactuar con Bodega y Fábrica

def despachar_producto(params: dict):
    # params contiene productoId, oc, direccion, precio
    auth_string = f'DELETE{params["productoId"]}{params["direccion"]}{params["precio"]}{params["oc"]}'
    auth_hash = hash_maker(auth_string)
    headers = {
        'Authorization': f'INTEGRACION grupo13:{auth_hash}',
        'Content-type': 'application/json',
    }
    response = requests.delete(
        f'{api_url}/stock',
        json=params,
        headers=headers
    )
    producto_bodega = ProductoBodega.objects.get(id=params["productoId"])
    sku = producto_bodega.sku
    producto_bodega.delete()
    producto_despachado = ProductoDespachado(
        id=params["productoId"], sku=sku, cliente=params["direccion"], oc_cliente=params["oc"], precio=params["precio"])
    producto_despachado.save()
    return response


def mover_entre_almacenes(params: dict):
    # params contiene productoId, almacenId
    auth_string = f'POST{params["productoId"]}{params["almacenId"]}'
    auth_hash = hash_maker(auth_string)
    headers = {
        'Authorization': f'INTEGRACION grupo13:{auth_hash}',
        'Content-type': 'application/json',
    }
    response = requests.post(
        f'{api_url}/moveStock',
        json=params,
        headers=headers
    )
    try:
        producto_bodega = ProductoBodega.objects.get(id=params["productoId"])
        producto_bodega.almacen = params["almacenId"]
        producto_bodega.save()
        return response
    except:
        return response


def mover_entre_bodegas(params: dict):
    # params contiene productoId, almacenId, oc, precio
    auth_string = f'POST{params["productoId"]}{params["almacenId"]}'
    auth_hash = hash_maker(auth_string)
    headers = {
        'Authorization': f'INTEGRACION grupo13:{auth_hash}',
        'Content-type': 'application/json',
    }
    response = requests.post(
        f'{api_url}/moveStockBodega',
        json=params,
        headers=headers
    )
    producto_bodega = ProductoBodega.objects.get(id=params["productoId"])
    sku_prod = producto_bodega.sku
    producto_bodega.delete()
    producto_despachado = ProductoDespachado(
        id=params["productoId"], sku=sku_prod, cliente=params["almacenId"], oc_cliente=params["oc"], precio=params["precio"])
    producto_despachado.save()
    return response


def obtener_almacenes():
    # no hay params porque es un GET
    auth_string = f'GET'
    auth_hash = hash_maker(auth_string)
    headers = {
        'Authorization': f'INTEGRACION grupo13:{auth_hash}',
        'Content-type': 'application/json',
    }
    response = requests.get(
        f'{api_url}/almacenes',
        headers=headers
    )
    return response


def obtener_productos_almacen(params: dict):
    # params contiene almacenId, sku, limit (opcionalmente, por defecto es 100)
    auth_string = f'GET{params["almacenId"]}{params["sku"]}'
    auth_hash = hash_maker(auth_string)
    headers = {
        'Authorization': f'INTEGRACION grupo13:{auth_hash}',
        'Content-type': 'application/json',
    }
    response = requests.get(
        f'{api_url}/stock?almacenId={params["almacenId"]}&sku={params["sku"]}',
        headers=headers
    )
    return response


def obtener_stock(params: dict):
    # params contiene almacenId
    auth_string = f'GET{params["almacenId"]}'
    auth_hash = hash_maker(auth_string)
    headers = {
        'Authorization': f'INTEGRACION grupo13:{auth_hash}',
        'Content-type': 'application/json',
    }
    response = requests.get(
        f'{api_url}/skusWithStock?almacenId={params["almacenId"]}',
        json=params,
        headers=headers
    )
    return response


def fabricar_producto(params: dict):
    # params contiene sku, cantidad
    print(params)
    sku = params["sku"]
    cantidad = int(params["cantidad"])
    lote = SKU_LOTE[sku]
    if cantidad <= lote:
        params["cantidad"] = lote
    else:
        params["cantidad"] = math.ceil(cantidad/lote)*lote
    auth_string = f'PUT{params["sku"]}{params["cantidad"]}'
    auth_hash = hash_maker(auth_string)
    headers = {
        'Authorization': f'INTEGRACION grupo13:{auth_hash}',
        'Content-type': 'application/json',
    }
    response = requests.put(
        f'{api_url}/fabrica/fabricarSinPago',
        json=params,
        headers=headers
    )
    fabricar = response.json()
    print(fabricar)
    log_pedido = Log(
        mensaje=f'Tu pedido de {fabricar["cantidad"]} unidades del sku {fabricar["sku"]} estaran disponibles el {fabricar["disponible"]}')
    log_pedido.save()
    pedido = Pedido(id=fabricar["_id"], sku=str(fabricar["sku"]), cantidad=params["cantidad"],
                    fecha_disponible=parse_js_date(fabricar["disponible"]))
    print("----------------------")
    pedido.save()
    return response


def fabricar_vacuna(params: dict):
    formulas = FORMULA
    productos_almacen = ProductoBodega.objects.filter(oc_reservada='')
    productos = {}
    ids_sku = {}
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
    ids_almacen = [almacen_recepcion['_id'], almacen_central['_id'],
                   almacen_pulmon['_id'], almacen_despacho['_id']]
    almacen_prod_id = {}
    ahora = utc.localize(datetime.now())
    vacuna_sku = params['tipo']
    keys = [key for key in formulas[vacuna_sku].keys()]
    for sku in keys:
        productos[sku] = 0

    for prod in productos_almacen:
        if ahora > prod.fecha_vencimiento:
            continue
        almacen_prod_id[prod.id] = prod.almacen
        if prod.sku in productos:
            productos[prod.sku] += 1
        else:
            productos[prod.sku] = 1
        if not prod.sku in ids_sku:
            ids_sku[prod.sku] = [prod.id]
        else:
            ids_sku[prod.sku].append(prod.id)
    has_stock = True
    names = {
        '10001': 'Pfizer',
        '10002': 'Sinovac',
        '10003': 'Astrazeneca',
        '10004': 'Janssen',
        '10005': 'Moderna',
        '10006': 'Sputnik'
    }

    available_skus = [key for key in productos.keys()]
    multiplicador = params['cantidad']/SKU_LOTE[vacuna_sku]
    print(multiplicador)
    try:
        has_stock = obtener_ingredientes(params['tipo'], productos, multiplicador)
        if not has_stock:
            log_no_sku = Log(mensaje=f'No tienes los ingredientes necesarios para fabricar el lote de vacunas {names[vacuna_sku]}')
            log_no_sku.save()
            return
        else:
            log_stock = Log(mensaje='Tienes stock suficiente para fabricar esta vacuna, vamos a mover los elementos necesarios a despacho!')
            log_stock.save()
            for ingrediente in FORMULA[vacuna_sku]:
                count = 0
                limit = int(FORMULA[vacuna_sku][ingrediente]*multiplicador)
                for id in ids_sku[ingrediente]:
                    if count == limit:
                        break
                    elif almacen_prod_id[id] != almacen_despacho['_id']:
                        time.sleep(1)
                        mover_entre_almacenes({ "productoId": id, "almacenId": almacen_despacho['_id']})
                        count += 1
                    else:
                        count += 1

            time.sleep(3)
            fabricar_producto({"sku": vacuna_sku, "cantidad": SKU_LOTE[vacuna_sku]})
            log_success = Log(mensaje=f'Se ha mandado a fabricar exitosamente un lote de vacunas {names[vacuna_sku]}')
            log_success.save()
    except Exception as err:
        error_log = Log(mensaje=f"{str(err)}")
        error_log.save()
        


def obtener_ingredientes(sku, productos, multiplicador):
    has_stock = True
    available_skus = [key for key in productos.keys()]
    print(productos)
    for ingrediente in FORMULA[sku]:
        time.sleep(2)
        print(f"{ingrediente}: tenemos disponible {productos[ingrediente]} y necesitamos {FORMULA[sku][ingrediente] * multiplicador}")
        if  (ingrediente not in available_skus) or (int(productos[ingrediente]) < int(FORMULA[sku][ingrediente])):
            has_stock = False
            if not ingrediente in NUESTRO_SKU:
                print('hay que pedir ' + ingrediente)
                index = randint(
                    0, len(PRODUCTOS[ingrediente]['Grupos Productores']) - 1)
                index_alt = randint(
                    0, len(PRODUCTOS[ingrediente]['Grupos Productores']) - 1)
                grupo = PRODUCTOS[ingrediente]['Grupos Productores'][index]
                grupo_alt = PRODUCTOS[ingrediente]['Grupos Productores'][index_alt]
                print('se lo pediremos a los grupos: ' + grupo + ' ' + grupo_alt)
                time.sleep(1)
                response = crear_oc(grupo, ingrediente, FORMULA[sku][ingrediente]*multiplicador)
                time.sleep(1)
                response_alt = crear_oc(grupo_alt, ingrediente, FORMULA[sku][ingrediente]*multiplicador)
                data = response.json()
                data_alt = response_alt.json()
                log_request = Log(mensaje=f'Acabas de hacer ordenes por el sku {ingrediente} a los grupos {grupo} y {grupo_alt}')
                log_request.save()
            else:
                response = fabricar_producto({'sku': ingrediente, 'cantidad': SKU_LOTE[ingrediente]*3})
                data = response.json()
        else: 
            continue
    return has_stock
