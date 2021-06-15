from rest_framework.parsers import JSONParser
from rest_framework import status
import requests
from hashlib import sha1
import hmac
import base64

api_url = 'https://dev.api-bodega.2021-1.tallerdeintegracion.cl/bodega'
clave_privada = '%@DP6wJYRuD$.D'

def hash_maker(msg:str):
    # función para hacer el hash para el header de Authorization
    hashed_string = hmac.new(bytes(clave_privada, 'utf-8'), bytes(msg, 'utf-8'), sha1)
    return base64.b64encode(hashed_string.digest()).decode()


# Funciones auxiliares para interactuar con Bodega y Fábrica

def despachar_producto(params:dict):
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
    return response

def mover_entre_almacenes():
    pass

def mover_entre_bodegas():
    pass

def obtener_almacenes():
    pass

def obtener_productos_almacen():
    pass

def obtener_stock():
    pass

def fabricar_producto():
    pass

