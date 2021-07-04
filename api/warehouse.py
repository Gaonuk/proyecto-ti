from rest_framework.parsers import JSONParser
from rest_framework import status
import requests
from hashlib import sha1
import hmac
import base64
from .models import Pedido, ProductoBodega, ProductoDespachado
from .OC import parse_js_date

#Only to define .env variables
import os
import environ
from pathlib import Path

#BASE DIRECTORY
BASE_DIR = Path(__file__).resolve().parent.parent

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
    # producto_bodega  = ProductoBodega.objects.get(id=params["productoId"]) 
    # sku = producto_bodega.sku
    # producto_bodega.delete()
    # producto_despachado = ProductoDespachado(id = params["productoId"],sku = sku, cliente = params["direccion"], oc_cliente = params["oc"], precio = params["precio"] )
    # producto_despachado.save()
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
    # producto_bodega  = ProductoBodega.objects.get(id=params["productoId"]) 
    # producto_bodega.almacen = params["almacenId"]
    # producto_bodega.save()
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
    # producto_bodega  = ProductoBodega.objects.get(id=params["productoId"]) 
    # sku_prod = producto_bodega.sku
    # producto_bodega.delete()
    # producto_despachado = ProductoDespachado(id = params["productoId"], sku = sku_prod, cliente = params["almacenId_externo"], oc_cliente = params["oc"], precio = params["precio"] )
    # producto_despachado.save()
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
    pedido = Pedido(id = fabricar["_id"], sku=fabricar["sku"], cantidad=params["cantidad"], fecha_disponible=parse_js_date(fabricar["disponible"]))
    pedido.save()
    return response

