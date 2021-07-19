from rest_framework.parsers import JSONParser
from rest_framework import status
import requests
from datetime import datetime, timedelta

#Only to define .env variables
import os
import environ
from pathlib import Path
from .models import SentOC, RecievedOC, Pedido, Log
from datetime import datetime
from .arrays_clients_ids_oc import IDS_DEV, IDS_PROD

if os.environ.get('DJANGO_DEVELOPMENT')=='true':
    ids_grupos = IDS_DEV
else:
    ids_grupos = IDS_PROD

#BASE DIRECTORY
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialise environment variables
env = environ.Env()
environ.Env.read_env(env_file= os.path.join(BASE_DIR, 'proyecto13/.env'))

URLS_GRUPOS = {
"60caa3af31df040004e88de4":    "http://aysen1.ing.puc.cl/ordenes-compra/",
"60caa3af31df040004e88de5":    "http://aysen2.ing.puc.cl/storage/ordenes-compra/",
"60caa3af31df040004e88de6":    "http://aysen3.ing.puc.cl/api/ordenes-compra/",
"60caa3af31df040004e88de7":    "http://aysen4.ing.puc.cl/ordenes-compra/",
"60caa3af31df040004e88de8":    "http://aysen5.ing.puc.cl/ordenes-compra/",
"60caa3af31df040004e88de9":    "http://aysen6.ing.puc.cl/ordenes-compra/",
"60caa3af31df040004e88dea":    "http://aysen7.ing.puc.cl/ordenes-compra/",
"60caa3af31df040004e88deb":    "http://aysen8.ing.puc.cl/ordenes-compra/",
"60caa3af31df040004e88dec":    "http://aysen9.ing.puc.cl/ordenes-compra/",
"60caa3af31df040004e88ded":    "http://aysen10.ing.puc.cl/ordenes-compra/",
"60caa3af31df040004e88dee":    "http://aysen11.ing.puc.cl/ordenes-compra/",
"60caa3af31df040004e88def":    "http://aysen12.ing.puc.cl/ordenes-compra/",
"60caa3af31df040004e88df0":    "http://aysen13.ing.puc.cl/ordenes-compra/",
"60caa3af31df040004e88df1":    "http://aysen14.ing.puc.cl/ordenes-compra/",
"60caa3af31df040004e88df2":    "http://aysen15.ing.puc.cl/ordenes-compra/",
"60caa3af31df040004e88df3":    "http://aysen16.ing.puc.cl/recepcionar/",
"60caa3af31df040004e88df4":    "http://aysen17.ing.puc.cl/ordenes-compra/",
"60caa3af31df040004e88df5":    "http://aysen18.ing.puc.cl/ordenes-compra/",
"60caa3af31df040004e88df6":    "http://aysen19.ing.puc.cl/ordenes-compra/",
"60caa3af31df040004e88df7":    "http://aysen20.ing.puc.cl/ordenes-compra/",
"60caa3af31df040004e88df8":    "http://aysen21.ing.puc.cl/ordenes-compra/",
"60caa3af31df040004e88df9":    "http://aysen22.ing.puc.cl/ordenes-compra/",
"60caa3af31df040004e88dfa":    "http://aysen23.ing.puc.cl/ordenes-compra/",
"60caa3af31df040004e88dfb":    "http://aysen24.ing.puc.cl/ordenes-compra/",
"60caa3af31df040004e88dfc":    "http://aysen25.ing.puc.cl/ordenes-compra/"
}

# URL de la API de órdenes de compra
if os.environ.get('DJANGO_DEVELOPMENT')=='true':
    api_url = env('API_OC_DEV')
else:
    api_url = env('API_OC_PROD')

def parse_js_date(date):
    date_format = date[:-1]
    return datetime.fromisoformat(date_format)

def parse_timestamp_date(date):
    return datetime.fromtimestamp(date/1000)


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

def pedir_producto(oc,tiempo):
    params = {
        "cliente": "60caa3af31df040004e88df0",
        "sku": oc["sku"],
        "urlNotificacion": oc["urlNotificacion"],
        "fechaEntrega": tiempo,
        "cantidad": oc["cantidad"]
    }
    headers = {
        'Content-type': 'application/json',
    }
    url = URLS_GRUPOS[oc["proveedor"]]
    response = requests.post(
        f'{url}{oc["_id"]}',
        headers=headers,
        json=params)

    return response

def crear_oc(grupo, sku, cantidad):
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
    ahora = datetime.now()
    startDate = datetime(1970, 1, 1)
    miliseconds = ahora - startDate + timedelta(hours=6)
    fecha_entrega = int(miliseconds.total_seconds() * 1000)
    params = {
        'cliente': ids_grupos[12],
        'proveedor': ids_grupos[int(grupo)-1],
        'sku': sku,
        'fechaEntrega': fecha_entrega, ####completar fecha
        'cantidad': cantidad,
        'precioUnitario': 1,
        'canal': 'b2b',
        'notas': 'dame dame',
        'urlNotificacion': 'http://aysen13.ing.puc.cl/ordenes-compra/{_id}'
    }

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
    respuesta = pedir_producto(oc, params["fechaEntrega"])
    if respuesta.status_code == 201:
        answer = respuesta.json()
        log_respuesta = Log(mensaje=f'OC de ID {answer["id"]} fue recibida')
        log_respuesta.save()
    pedido = Pedido(id = oc["_id"], sku =str(oc["sku"]), cantidad=oc["cantidad"], fecha_disponible=parse_js_date(oc["fechaEntrega"]))
    pedido.save()
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
        headers=headers,
        json={}
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