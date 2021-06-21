from rest_framework.parsers import JSONParser
from rest_framework import status
import requests

#Only to define .env variables
import os
import environ
from pathlib import Path
from .models import SentOC, RecievedOC
from datetime import datetime

#BASE DIRECTORY
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialise environment variables
env = environ.Env()
environ.Env.read_env(env_file= os.path.join(BASE_DIR, 'proyecto13/.env'))


# URL de la API de órdenes de compra
if os.environ.get('DJANGO_DEVELOPMENT')=='true':
    api_url = env('API_OC_DEV')
else:
    api_url = env('API_OC_PROD')

def parse_js_date(date):
    date_format = date[:-1]
    return datetime.fromisoformat(date_format)


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
        headers=headers,
        json=params
    )
    return response

def crear_oc(params:dict):
    # Parámetros recibidos:
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
        headers=headers,
        json=params
    )
    oc = response.json()
    sent_oc = SentOC(id=oc["_id"], cliente=oc["cliente"], proveedor=oc["proveedor"],sku=oc["sku"],fecha_entrega=parse_js_date(oc["fechaEntrega"]),
    cantidad=oc["cantidad"], cantidad_despachada=oc["cantidadDespachada"], precio_unitario=oc["precioUnitario"], canal=oc["canal"],
    estado=oc["estado"], created_at=parse_js_date(oc["created_at"]), updated_at=parse_js_date(oc["updated_at"]))
    if "notas" in oc.keys():
        sent_oc.notas = oc["notas"]
    if "rechazo" in oc.keys():
        sent_oc.rechazo = oc["rechazo"]
    if "anulacion" in oc.keys():
        sent_oc.anulacion = oc["anulacion"]
    if "urlNotificacion" in oc.keys():
        sent_oc.url_notificaion = oc["urlNotificacion"]
    sent_oc.save()
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
    oc = RecievedOC.objects.get(id=id)
    oc.estado = "aceptada"
    oc.save()
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
        headers=headers,
        json=params
    )
    oc = RecievedOC.objects.get(id=id)
    oc.estado = "rechazada"
    oc.save()
    return response