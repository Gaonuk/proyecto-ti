from rest_framework.parsers import JSONParser
from rest_framework import status
import requests
from hashlib import sha1
import hmac
import base64
from .models import Log, Pedido, ProductoBodega, ProductoDespachado
from .OC import parse_js_date

import time
import math


#Only to define .env variables
import os
import environ
from pathlib import Path

#BASE DIRECTORY
BASE_DIR = Path(__file__).resolve().parent.parent

SKU_LOTE = {
    '107': 7,
    '100': 5,
    '108': 18,
    '112': 5,
    '113': 12,
    '114': 14,
    '118': 4,
    '119': 14,
    '129': 10,
    '115': 20,
    '120': 5,
    '121': 3,
    '126': 10,
    '127': 5,
    '132': 14,
    '110': 6,
    '103': 9,
    '102': 8,
    '1000': 8,
    '1001': 5,
    '10001': 6,
    '10002': 8,
    '10005': 4,

}

# Initialise environment variables
env = environ.Env()
environ.Env.read_env(env_file= os.path.join(BASE_DIR, 'proyecto13/.env'))


if os.environ.get('DJANGO_DEVELOPMENT')=='true':
    api_url = env('API_BODEGA_DEV')
    clave_privada = env('CLAVE_BODEGA_DEV')
else:
    api_url = env('API_BODEGA_PROD')
    clave_privada = env('CLAVE_BODEGA_PROD')

def hash_maker(msg:str):
    # función para hacer el hash para el header de Authorization
    hashed_string = hmac.new(bytes(clave_privada, 'utf-8'), bytes(msg, 'utf-8'), sha1)
    return base64.b64encode(hashed_string.digest()).decode()


# Funciones auxiliares para interactuar con Bodega y Fábrica

def despachar_producto(params:dict):
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
    producto_bodega  = ProductoBodega.objects.get(id=params["productoId"]) 
    sku = producto_bodega.sku
    producto_bodega.delete()
    producto_despachado = ProductoDespachado(id = params["productoId"],sku = sku, cliente = params["direccion"], oc_cliente = params["oc"], precio = params["precio"] )
    producto_despachado.save()
    return response

def mover_entre_almacenes(params:dict):
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
        producto_bodega  = ProductoBodega.objects.get(id=params["productoId"]) 
        producto_bodega.almacen = params["almacenId"]
        producto_bodega.save()
        return response
    except:
        return response

def mover_entre_bodegas(params:dict):
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
    producto_bodega  = ProductoBodega.objects.get(id=params["productoId"]) 
    sku_prod = producto_bodega.sku
    producto_bodega.delete()
    producto_despachado = ProductoDespachado(id = params["productoId"], sku = sku_prod, cliente = params["almacenId_externo"], oc_cliente = params["oc"], precio = params["precio"] )
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

def obtener_productos_almacen(params:dict):
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

def obtener_stock(params:dict):
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

def fabricar_producto(params:dict):
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
    log_pedido = Log(mensaje=f'Tu pedido de {fabricar["cantidad"]} unidades del sku {fabricar["sku"]} estaran disponibles el {fabricar["disponible"]}')
    log_pedido.save()
    pedido = Pedido(id = fabricar["_id"], sku=str(fabricar["sku"]), cantidad=params["cantidad"], \
        fecha_disponible=parse_js_date(fabricar["disponible"]))
    print("----------------------")
    pedido.save()
    return response

def fabricar_vacuna(params:dict):
    formulas = {
        '10001': {
            '1000': 12, 
            '108': 6, 
            '107': 6, 
            '100': 6, 
            '114': 6, 
            '112': 6, 
            '119': 6, 
            '129': 12, 
            '113': 6, 
            '118': 6
        }, 
        '10002': {
            '1001': 8, 
            '121': 8, 
            '120': 16, 
            '115': 8, 
            '113': 16
        }, 
        '10005': {
            '1000': 12, 
            '126': 4, 
            '114': 4, 
            '100': 4, 
            '127': 4, 
            '132': 8, 
            '110': 4, 
            '103': 4, 
            '102': 4, 
            '129': 4
        }
    }
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
    ids_almacen = [almacen_recepcion['_id'], almacen_central['_id'], almacen_pulmon['_id'], almacen_despacho['_id']]
    almacen_prod_id = {}
    for prod in productos_almacen:
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
    vacuna_sku = params['tipo']
    lote_sku = {
        '10001': 6,
        "10002": 8,
        "10005": 4
    }
    names = {
        '10001': 'Pfizer',
        '10002': 'Sinovac',
        '10005': 'Moderna'
    }
    log_vacuna = Log(mensaje=f"Se esta intentando fabricar un lote de vacuna {names[vacuna_sku]}")
    log_vacuna.save()
    
    keys = [key for key in formulas[vacuna_sku].keys()]
    available_skus = [key for key in productos.keys()]
    try:
        for sku in keys:
            if not sku in available_skus:
                log_no_sku = Log(mensaje=f'No tienes el sku {sku}, necesario para fabricar el lote de vacunas {names[vacuna_sku]}')
                log_no_sku.save()
                has_stock = False
                break
            else:
                if productos[sku] < formulas[vacuna_sku][sku]:
                    log_no_stock = Log(mensaje=f'No tienes stock suficiente de sku {sku} para fabricar el lote de vacunas {names[vacuna_sku]}')
                    log_no_stock.save()
                    has_stock = False
                    break
        if has_stock:
            log_stock = Log(mensaje='Tienes stock suficiente para fabricar esta vacuna, vamos a mover los elementos necesarios a despacho!')
            log_stock.save()
            for sku in keys: 
                count = 0
                limit = formulas[vacuna_sku][sku]
                for id in ids_sku[sku]:
                    if count == limit:
                        break
                    elif almacen_prod_id[id] != almacen_despacho['_id']:
                        mover_entre_almacenes({ "productoId": id, "almacenId": almacen_despacho['_id']})
                        time.sleep(1)
                        count += 1
                    else:
                        count += 1
                        
            fabricar_producto({"sku": vacuna_sku, "cantidad": lote_sku[vacuna_sku]})
            log_success = Log(mensaje=f'Se ha mandado a fabricar exitosamente un lote de vacunas {names[vacuna_sku]}')
            log_success.save()
    except Exception as err:
        error_log = Log(mensaje=f"{err}")
        error_log.save()
