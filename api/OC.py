from rest_framework.parsers import JSONParser
from rest_framework import status
import requests
from hashlib import sha1
import hmac
import base64

# URL de la API de órdenes de compra
api_url = 'https://dev.oc.2021-1.tallerdeintegracion.cl/oc'


def anular_oc(id, params:dict):
    # Recibe el id de la orden de compra
    #Y un mensaje de la razón de pq se anuló, ejemplo:
#     {
#    "anulacion": "Anulada por cantidad incorrecta"
#       }
    headers = {
        'Content-type': 'application/json',
    }
    response = requests.delete(
        f'{api_url}/anular/{id}',
        headers=headers
        json=params
    )
    return response

def crear_oc(params:dict):
    # NO tiene param porque crea una OC nueva, parámetros recibidos:
    # Ejemplo de datos enviados en json
#     {
#     "cliente": "4af9f23d8ead0e1d320000a1",
#     "proveedor": "4af9f23d8ead0e1d320000b2",
#     "sku": "45",
#     "fechaEntrega": 4493214596281,
#     "cantidad": "10",
#     "precioUnitario": "100",
#     "canal": "b2b",
#     "notas": "SegundaCreacion",
#     "urlNotificacion": "http://example.com/{_id}/notification"
# }
    headers = {
        'Content-type': 'application/json',
    }
    response = requests.put(
        f'{api_url}/crear',
        headers=headers
        json=params
    )
    return response

def obtener_oc(id):
    # Recibe solamente un ID de OC
    headers = {
        'Content-type': 'application/json',
    }
    response = requests.get(
        f'{api_url}/obtener/{id}',
        headers=headers
    )
    return response

def recepcionar_oc(id):
    # Recibe solo el ID de la OC
    #No es necesario pasar params aunque
    #La documentación lo diga
    headers = {
        'Content-type': 'application/json',
    }
    response = requests.post(
        f'{api_url}/recepcionar/{id}',
        headers=headers
    )
    return response

def rechazar_oc(id,params:dict):
    # Se recibe un id de rechazo
    #Se recibe un mensaje de la razón de rechazon en el json, ejemplo:
#     {
#     "rechazo": "Rechazada por monto incorrecto"
#       }
    headers = {
        'Content-type': 'application/json',
    }
    response = requests.post(
        f'{api_url}/rechazar/{id}',
        headers=headers
        json=params
    )
    return response