from api.business_logic import factibildad
from django.shortcuts import render
from requests.api import post
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.decorators import api_view
from django.http.response import JsonResponse
from rest_framework.response import Response
from .warehouse import despachar_producto, fabricar_vacuna, mover_entre_almacenes, mover_entre_bodegas, obtener_almacenes, obtener_productos_almacen, obtener_stock, fabricar_producto

from .forms import FormActualizarMaxOCIngredientes, FormCambiarAlmacen, FormCambiarBodega, FormCambiarAlmacenPorSKU, FormCrearVacuna, FormFabricar, FormCrearOC, FormActualizarMaxOCVacunas
from django.http import HttpResponseRedirect
from django.contrib import messages

from .OC import obtener_oc, recepcionar_oc, rechazar_oc, parse_js_date, crear_oc
from .models import CantidadMaxAceptada, ProductoBodega, RecievedOC, SentOC, Log, ProductoDespachado, EmbassyOC
from random import randint, random, uniform
import requests
import json

from .business_logic import factibildad

# Create your views here.
from .arrays_almacenes_recep import RECEPCIONES_DEV, RECEPCIONES_PROD
from datetime import datetime, timedelta
from .arrays_clients_ids_oc import IDS_DEV, IDS_PROD
from .INFO_SKU.info_sku import PRODUCTOS, FORMULA, NUESTRO_SKU, FORMULA_COMPLETA

# Endpoints que exponemos para otros grupos
import environ
import os
from pathlib import Path

# BASE DIRECTORY
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
    '10003': 5,
    '10004': 5,
    '10006': 9,

}

# Initialise environment variables
env = environ.Env()
environ.Env.read_env(env_file=os.path.join(BASE_DIR, 'proyecto13/.env'))


if os.environ.get('DJANGO_DEVELOPMENT')=='true':
    cliente = '60bd2a763f1b6100049f1453'
    ids_oc = IDS_DEV
else:
    cliente = '60caa3af31df040004e88df0'
    ids_oc = IDS_PROD



if os.environ.get('DJANGO_DEVELOPMENT')=='true':
    TITULO_RECEPCIONES = 'ALMACENES EXTERNOS DEV'
    ALMACENES_RECEPCION_EXT = RECEPCIONES_DEV
else:
    TITULO_RECEPCIONES = 'ALMACENES EXTERNOS PROD'
    ALMACENES_RECEPCION_EXT = RECEPCIONES_PROD


@api_view(['GET'])
def consulta_stock(request):
    if request.method == 'GET':
        sku_stocks = {}
        almacenes = obtener_almacenes().json()
        for almacen in almacenes:
            # Depende de nosotros consultar todos los almacenes o no
            # if almacen['despacho']:
            #     continue
            params = {'almacenId': almacen['_id']}
            # print(almacen['_id'])
            stock = obtener_stock(params).json()
            # print(stock)
            for producto in stock:
                if producto['_id'] in sku_stocks:
                    sku_stocks[producto['_id']] += producto['total']
                else:
                    sku_stocks[producto['_id']] = producto['total']
        response = []
        for sku in sku_stocks:
            response.append({
                'sku': sku,
                'total': sku_stocks[sku],
            })
        return Response(response, status=status.HTTP_200_OK)

    else:  # En caso de un method nada que ver
        return Response(
            {'message': f'{request.method} method not allowed for this request'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

SKU_PRODUCCION_PROPIOS = {
    '108': 25,
    '119': 45,
    '129': 15,
    '121': 30,
    '132': 15,
    '1000': 50,
    '1001': 40,
    '10001': 35,
    '10002': 25,
    '10005': 40,
}

@api_view(['POST', 'PATCH'])
def manejo_oc(request, id):
    body = json.loads(request.body)
    if request.method == 'POST':

        if RecievedOC.objects.filter(id=id).exists():
            with open('registro_oc.txt', 'a') as registro:
                registro.write(f'POST-400: OC {id} - {datetime.now()}\n')
            return Response({'message': 'OC ya fue recibida'},
                            status=status.HTTP_400_BAD_REQUEST)
        else:
            # Momento de recepci??n en un txt
            with open('registro_oc.txt', 'a') as registro:
                registro.write(f'POST-201: OC {id} - {datetime.now()}\n')

            orden_de_compra = obtener_oc(id).json()[0]
            if orden_de_compra["sku"] not in SKU_PRODUCCION_PROPIOS.keys():
                return Response({'message': 'El sku no es fabricado por este grupo.'},
                                status=status.HTTP_400_BAD_REQUEST)
            if orden_de_compra["cliente"] not in ids_oc:
                return Response({'message': 'Cliente no existe'},
                                status=status.HTTP_400_BAD_REQUEST)
            if orden_de_compra["proveedor"] != cliente:
                return Response({'message': 'No somos el proveedor de esta OC'},
                                status=status.HTTP_400_BAD_REQUEST)
            if orden_de_compra["canal"] not in ["b2b", "b2c", "ftp"]:
                return Response({'message': 'El canal no corresponde'},
                                status=status.HTTP_400_BAD_REQUEST)
            if orden_de_compra["estado"] not in ["creada", "aceptada", "rechazada", "finalizada", "anulada"]:
                return Response({'message': 'El estado de la OC no corresponde'},
                                status=status.HTTP_400_BAD_REQUEST)
            if parse_js_date(orden_de_compra["fechaEntrega"]) < datetime.now():
                return Response({'message': 'La fecha de entrega ya paso'},
                                status=status.HTTP_400_BAD_REQUEST)
            oc = RecievedOC(id=id,
                            cliente=orden_de_compra["cliente"],
                            proveedor=orden_de_compra["proveedor"],
                            sku=orden_de_compra["sku"],
                            fecha_entrega=parse_js_date(
                                orden_de_compra["fechaEntrega"]),
                            cantidad=orden_de_compra["cantidad"],
                            cantidad_despachada=orden_de_compra["cantidadDespachada"],
                            precio_unitario=orden_de_compra["precioUnitario"],
                            canal=orden_de_compra["canal"],
                            estado=orden_de_compra["estado"],
                            created_at=parse_js_date(
                                orden_de_compra["created_at"]),
                            updated_at=parse_js_date(
                                orden_de_compra["updated_at"])
                            )

            if "notas" in orden_de_compra.keys():
                oc.notas = orden_de_compra["notas"]
            if "rechazo" in orden_de_compra.keys():
                oc.rechazo = orden_de_compra["rechazo"]
            if "anulacion" in orden_de_compra.keys():
                oc.anulacion = orden_de_compra["anulacion"]
            if "urlNotificacion" in orden_de_compra.keys():
                oc.url_notification = orden_de_compra["urlNotificacion"]
            oc.save()
            if orden_de_compra["urlNotificacion"] == "":
                url= body["urlNotificacion"]
            else:
                url = orden_de_compra["urlNotificacion"]

            oc_es_factible = factibildad(oc.sku, oc.cantidad, oc.fecha_entrega, oc.id)

            # if uniform(0,1) <= 0.3:
            if oc_es_factible:
                factibildad(oc.sku, oc.cantidad, oc.fecha_entrega, oc.id )
                recepcionar_oc(id)
                params = json.dumps({"estado": "aceptada"})
                headers = {'Content-type': 'application/json'}
                requests.patch(url=url, data=params, headers=headers)
                
                log_aceptacion = Log(mensaje=f'Manejo OC {id}: Fue aceptada dentro del 5% de probabilidad')
                log_aceptacion.save()
            else:
                rechazar_oc(id, {"rechazo": "No podemos despachar"})
                params = json.dumps({"estado": "rechazada"})
                headers = {'Content-type': 'application/json'}
                requests.patch(url=url, data=params, headers=headers)
                log_rechazo = Log(mensaje=f'Manejo OC {id}: Fue rechazada por nosotros')
                log_rechazo.save()
            response = {"id": id,
                        "cliente": body["cliente"],
                        "sku": body["sku"],
                        "fechaEntrega": body["fechaEntrega"],
                        "cantidad": body["cantidad"],
                        "urlNotificacion": body["urlNotificacion"],
                        "estado": "recibida"}

            return Response(response, status=status.HTTP_201_CREATED)

    elif request.method == 'PATCH':
        body = json.loads(request.body)
        estado = body["estado"]
        log_oc = Log(mensaje=f'La OC de ID: {id} fue {estado}')
        log_oc.save()
        if SentOC.objects.filter(id=id).exists():
            # Momento de recepci??n en un txt
            with open('registro_oc.txt', 'a') as registro:
                registro.write(f'PATCH-204: OC {id} - {datetime.now()}\n')
            sent_oc = SentOC.objects.get(id=id)
            sent_oc.estado = estado
            sent_oc.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            with open('registro_oc.txt', 'a') as registro:
                registro.write(f'PATCH-404: OC {id} - {datetime.now()}\n')
            return Response(status=status.HTTP_404_NOT_FOUND)

    else:  # En caso de un method nada que ver
        return Response(
            {'message': f'{request.method} method not allowed for this request'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )


@api_view(['GET', 'POST', 'DELETE', 'PUT'])  # para que sirve esto
def algun_endopint(request, algun_id):
    # Si el URL que llama este endpoint tiene alguna variable,
    # debe ir en el input de la funci??n, junto a request.
    if request.method == 'GET':  # ejemplo para obtener todas las instancias de un modelo        artists = Artist.objects.all()
        # algunos_modelos = AlgunModelo.objects.all()
        # algun_serializer = AlgunSerializer(algunos_modelos, many=True)
        # for instancia in algun_serializer.data:
        #     # Hago alguna magia con la data
        #     data = {"campo": "valor"}
        # return JsonResponse(response, safe=False)
        pass
    elif request.method == 'POST':
        # data = JSONParser().parse(request) # Hacer algo con la info del POST
        # algun_serializer = AlgunSerializer(data=data)
        # if algun_serializer.is_valid():
        #     algun_serializer.save()
        #     return Response({'message': 'POST was made succesfully'} , status=status.HTTP_200_OK)
        # return Response(algun_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        pass
    elif request.method == 'PUT':  # Ejemplo para reproducir las canciones de un album
        # tracks = Track.objects.filter(album=album_id)
        # for track in tracks:
        #     track.times_played += 1
        #     track.save()
        # return Response({'message': 'The tracks were played succesfully'} , status=status.HTTP_200_OK)
        pass

    elif request.method == 'DELETE':
        # Para un delete, generalmente querr?? borrar algo espec??fico
        # por lo que necesitar??a una variable del URL
        # loquequieroborrar = AlgunModelo.objects.get(pk=algun_id)
        # loquequieroborrar.delete()
        # return Response({'message': 'Something was deleted succesfully'} , status=status.HTTP_204_NO_CONTENT)
        pass

    else:  # En caso de un method nada que ver
        return Response(
            {'message': f'{request.method} method not allowed for this request'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )


def index(request):
    vacunas_fabricadas = {
        "Pfizer": 0,
        "Sinovac": 0,
        "Moderna": 0,
        "Astrazeneca": 0,
        "Janssen": 0,
        "Sputnik": 0
    }
    # Informaci??n de los almacenes
    almacenes = obtener_almacenes().json()
    info_almacenes = {}
    for almacen in almacenes:
        id = almacen["_id"]
        used = almacen["usedSpace"]
        total = almacen["totalSpace"]
        if almacen["recepcion"]:
            info_almacenes['Recepci??n'] = [id, used, total]
        if almacen["despacho"]:
            info_almacenes['Despacho'] = [id, used, total]
        if almacen["pulmon"]:
            info_almacenes['Pulm??n'] = [id, used, total]
        if almacen["pulmon"] == False and almacen["despacho"] == False and almacen["recepcion"] == False:
            info_almacenes['Central'] = [id, used, total]
        almacen["almacenId"] = almacen["_id"]
    labels_almacenes = ['Recepci??n', 'Despacho', 'Pulm??n', 'Central']
    ocupacion_almacenes = [info_almacenes[i][1] for i in labels_almacenes]
    id_almacenes = [info_almacenes[i][0] for i in labels_almacenes]
    # Informaci??n stock disponible de vacunas y compuestos
    cantidad_sku = {}
    for almacen in almacenes:
        sku_almacen = obtener_stock(almacen).json()
        for sku in sku_almacen:
            if sku["_id"] in cantidad_sku:
                cantidad_sku[sku["_id"]] += int(sku["total"])
            else:
                cantidad_sku[sku["_id"]] = int(sku["total"])
    labels_stock = [key for key in cantidad_sku.keys()]
    stock = [cantidad_sku[i] for i in labels_stock]

    # orden_de_compra = obtener_oc("60d0ba39e72508000448529d").json()[0]
    # oc = SentOC(id="60d0ba39e72508000448529d", cliente=orden_de_compra["cliente"], proveedor=orden_de_compra["proveedor"],
    #                 sku=orden_de_compra["sku"], fecha_entrega=parse_js_date(orden_de_compra["fechaEntrega"]), cantidad=orden_de_compra["cantidad"],
    #                 cantidad_despachada=orden_de_compra[
    #                     "cantidadDespachada"], precio_unitario=orden_de_compra["precioUnitario"],
    #                 canal=orden_de_compra["canal"], estado=orden_de_compra["estado"], created_at=parse_js_date(
    #                     orden_de_compra["created_at"]),
    #                 updated_at=parse_js_date(orden_de_compra["updated_at"]))

    # if "notas" in orden_de_compra.keys():
    #     oc.notas = orden_de_compra["notas"]
    # if "rechazo" in orden_de_compra.keys():
    #     oc.rechazo = orden_de_compra["rechazo"]
    # if "anulacion" in orden_de_compra.keys():
    #     oc.anulacion = orden_de_compra["anulacion"]
    # if "urlNotificacion" in orden_de_compra.keys():
    #     oc.url_notification = orden_de_compra["urlNotificacion"]
    # oc.save()
    productos = ProductoDespachado.objects.all()
    productos_grupo = {}
    productos_sku = {}
    for p in productos:
        if int(prod.sku) == 10001:
            vacunas_fabricadas['Pfizer'] += 1
        elif int(prod.sku) == 10002:
            vacunas_fabricadas['Sinovac'] += 1
        elif int(prod.sku) == 10005:
            vacunas_fabricadas['Moderna'] += 1
        elif int(prod.sku) == 10003:
            vacunas_fabricadas['Astrazeneca'] += 1
        elif int(prod.sku) == 10004:
            vacunas_fabricadas['Janssen'] += 1
        elif int(prod.sku) == 10006:
            vacunas_fabricadas['Sputnik'] += 1
        grupo = ALMACENES_RECEPCION_EXT.index(p.cliente) + 1
        if grupo in productos_grupo and p.sku in productos_sku:
            productos_grupo[grupo] += 1
            productos_sku[p.sku] += 1
        elif grupo in productos_grupo and p.sku not in productos_sku:
            productos_grupo[grupo] += 1
            productos_sku[p.sku] = 1
        elif grupo not in productos_grupo and p.sku in productos_sku:
            productos_grupo[grupo] = 1
            productos_sku[p.sku] += 1
        else:
            productos_sku[p.sku] = 1
            productos_grupo[grupo] = 1
    productos_bodega = ProductoBodega.objects.all()
    for prod in productos_bodega:
        if int(prod.sku) == 10001:
            vacunas_fabricadas['Pfizer'] += 1
        elif int(prod.sku) == 10002:
            vacunas_fabricadas['Sinovac'] += 1
        elif int(prod.sku) == 10005:
            vacunas_fabricadas['Moderna'] += 1
        elif int(prod.sku) == 10003:
            vacunas_fabricadas['Astrazeneca'] += 1
        elif int(prod.sku) == 10004:
            vacunas_fabricadas['Janssen'] += 1
        elif int(prod.sku) == 10006:
            vacunas_fabricadas['Sputnik'] += 1

    labels_grupo = [key for key in productos_grupo.keys()]
    prods_grupo = [productos_grupo[i] for i in labels_grupo]

    labels_sku = [key for key in productos_sku.keys()]
    prods_sku = [productos_sku[i] for i in labels_sku]

    labels_vacunas = [key for key in vacunas_fabricadas.keys()]
    prods_vacunas = [vacunas_fabricadas[i] for i in labels_vacunas]

    return render(request, 'index.html', {'params': {'labels_almacenes': labels_almacenes, 'ocupacion_almacenes': ocupacion_almacenes,
                                                     'labels_stock': labels_stock, 'stock': stock,
                                                     'labels_grupo': labels_grupo, "prods_grupo": prods_grupo,
                                                     "labels_sku": labels_sku, 'prods_sku': prods_sku,
                                                     "labels_vacunas": labels_vacunas, "prods_vacunas": prods_vacunas
                                                     }})


def logs(request):
    logs = Log.objects.all().order_by('-created_at')
    return render(request, 'logs.html', {'logs': logs})


def backoffice(request):
    # Arrays para hacer comparativas
    # antes de enviar el POST
    IDs_almacenes = []
    IDs_productos = []
    IDs_por_sku = {}
    # Obtenemos todos los almacenes
    almacenes = obtener_almacenes().json()
    for almacen in almacenes:
        # Creamos una nueva variable 'id' porque front no permite "_"
        almacen['id'] = almacen['_id']
        params = {'almacenId': almacen['_id']}
        # Para cada almac??n vemos su stock
        stock = obtener_stock(params).json()
        # Guardamos los IDs de los almacenes en un Array
        IDs_almacenes.append(almacen['_id'])
        # Guardamos en el mismo objeto los productos del almacen
        almacen['productos'] = stock
        # Guardamos la cantidad de productos del almacen para hacer un IF en el front
        almacen['cant_productos'] = len(stock)
        # Este array sirve para guardar por SKU todos los IDs de productos en el mismo objeto de almac??n
        almacen['detalle_productos'] = {}
        print(stock)
        # Si hay productos en el almacen, iteramos sobre ellos
        IDs_por_sku[almacen['_id']] = {}
        if len(stock) > 0:
            for sku in stock:
                # Vamos a guardar en un objeto los SKUs y un array con sus IDs para ser usado en otro m??todo
                IDs_por_sku[almacen['_id']][sku['_id']] = []
                # Sacamos todos los IDs por SKU
                productos_almacen = obtener_productos_almacen(
                    {"almacenId": almacen['_id'], "sku": sku["_id"]}).json()
                for producto_almacen in productos_almacen:
                    # Aqu?? se guardan todos los ID's por SKU y por almacen
                    IDs_por_sku[almacen['_id']][sku['_id']].append(
                        producto_almacen['_id'])
                    # Creamos una nueva variable 'id' porque front no permite "_"
                    producto_almacen['id'] = producto_almacen['_id']
                    IDs_productos.append(producto_almacen["_id"])
                # Guardamos todos los productos seg??n SKU en un objeto
                almacen['detalle_productos'][sku["_id"]] = productos_almacen

    if request.method == 'POST':
        # print(request.POST.get('cantidad'))
        # print(request.POST.get('SKU'))
        if request.POST.get('max_ing', '') != '':
            form_cambiar_almacen = FormCambiarAlmacen()
            form_cambiar_bodega = FormCambiarBodega()
            form_fabricar = FormFabricar()
            form_cambiar_almacen_SKU = FormCambiarAlmacenPorSKU()
            form_crear_oc = FormCrearOC()
            form_actualizar_oc_ingredientes = FormActualizarMaxOCIngredientes(request.POST)
            form_actualizar_oc_vacunas = FormActualizarMaxOCVacunas()
            try: 
                max_ingredientes = CantidadMaxAceptada.objects.get(pk='ingredientes')
                max_ingredientes.cantidad = request.POST.get('max_ing')
                max_ingredientes.save()

            except CantidadMaxAceptada.DoesNotExist: 
                max_ingredientes = CantidadMaxAceptada(
                    tipo_oc = 'ingredientes',
                    cantidad = 10
                )
                max_ingredientes.save()

            return HttpResponseRedirect('/backoffice')

        elif request.POST.get('max_vac', '') != '':
            form_cambiar_almacen = FormCambiarAlmacen()
            form_cambiar_bodega = FormCambiarBodega()
            form_fabricar = FormFabricar()
            form_cambiar_almacen_SKU = FormCambiarAlmacenPorSKU()
            form_crear_oc = FormCrearOC()
            form_actualizar_oc_ingredientes = FormActualizarMaxOCIngredientes()
            form_actualizar_oc_vacunas = FormActualizarMaxOCVacunas(request.POST)
            try: 
                max_vacunas = CantidadMaxAceptada.objects.get(pk='vacunas')
                max_vacunas.cantidad = request.POST.get('max_vac')
                max_vacunas.save()

                
            except CantidadMaxAceptada.DoesNotExist: 
                max_vacunas = CantidadMaxAceptada(
                    tipo_oc = 'vacunas',
                    cantidad = 10
                )
                max_vacunas.save()
            return HttpResponseRedirect('/backoffice')

        elif request.POST.get('oc', '') == '' and request.POST.get('SKU', '') == '' and request.POST.get('cantidad', '') == '':
            print('primer if')
            form_cambiar_bodega = FormCambiarBodega()
            form_cambiar_almacen = FormCambiarAlmacen(request.POST)
            form_cambiar_almacen_SKU = FormCambiarAlmacenPorSKU()
            form_fabricar = FormFabricar()
            form_crear_oc = FormCrearOC()
            form_actualizar_oc_ingredientes = FormActualizarMaxOCIngredientes()
            form_actualizar_oc_vacunas = FormActualizarMaxOCVacunas()
            # print(IDs_almacenes)
            # print(IDs_productos)
            ID_producto = request.POST.get('productoId', '')
            ID_almacen = request.POST.get('almacenId', '')
            if form_cambiar_almacen.is_valid():
                post_valido = True
                if ID_almacen not in IDs_almacenes:
                    messages.warning(
                        request, '??El ID de este almac??n NO existe!')
                    post_valido = False
                if ID_producto not in IDs_productos:
                    messages.warning(
                        request, '??El ID de este producto NO existe!')
                    post_valido = False
                if post_valido:
                    mover_entre_almacenes(
                        {'productoId': ID_producto, "almacenId": ID_almacen})
                    messages.info(
                        request, 'El producto ha sido cambiado de almac??n')
                    return HttpResponseRedirect('/backoffice')

        elif request.POST.get('proveedor', '') != '':
            valid_SKUs = [
                '100',
                '107',
                '108',
                '112',
                '113',
                '114',
                '118',
                '119',
                '129',
                '115',
                '120',
                '121',
                '126',
                '127',
                '132',
                '110',
                '103',
                '102',
                '1000',
                '1001',
                '10001',
                '10002',
                '10005'                
            ]
            form_cambiar_bodega = FormCambiarBodega()
            form_cambiar_almacen = FormCambiarAlmacen()
            form_cambiar_almacen_SKU = FormCambiarAlmacenPorSKU()
            form_fabricar = FormFabricar()
            form_crear_oc = FormCrearOC(request.POST)
            form_actualizar_oc_ingredientes = FormActualizarMaxOCIngredientes()
            form_actualizar_oc_vacunas = FormActualizarMaxOCVacunas()
            proveedor = request.POST.get('proveedor')
            SKU = request.POST.get('SKU')
            fechaEntrega = request.POST.get('fechaEntrega')
            cantidad = request.POST.get('cantidad')
            precio = request.POST.get('precio')
            canal = request.POST.get('canal')
            notas = request.POST.get('notas')
            urlNotificacion = request.POST.get('urlNotificacion')
            date, time = fechaEntrega.split(';')
            day, month, year = date.split('/')
            hour, minutes, seconds = time.split(':')
            dateTime = datetime(int(year), int(month), int(
                day), int(hour), int(minutes), int(seconds))
            startDate = datetime(1970, 1, 1)
            miliseconds = dateTime - startDate + timedelta (hours=4)
            print(int(miliseconds.total_seconds() * 1000))
            if form_crear_oc.is_valid():
                post_valido = True
                if SKU not in valid_SKUs:
                    messages.warning(request, '??Este SKU NO existe!')
                    post_valido = False
                if post_valido:
                    if urlNotificacion != "":
                        response = crear_oc({"cliente": cliente, "proveedor": proveedor, "sku": SKU, "fechaEntrega": int(miliseconds.total_seconds(
                        ) * 1000), "cantidad": cantidad, "precioUnitario": precio, "canal": canal, "urlNotificacion": urlNotificacion, "notas": notas})
                        data = response.json()
                        messages.info(request, f"{data}")
                    else:
                        response = crear_oc({"cliente": cliente, "proveedor": proveedor, "sku": SKU, "fechaEntrega": int(
                            miliseconds.total_seconds() * 1000), "cantidad": cantidad, "precioUnitario": precio, "canal": canal})
                        data = response.json()
                        messages.info(request, f"{data}")

        elif request.POST.get('oc', '') != '' and request.POST.get('SKU', '') == '' and request.POST.get('cantidad', '') == '':
            form_cambiar_almacen = FormCambiarAlmacen()
            form_cambiar_bodega = FormCambiarBodega(request.POST)
            form_cambiar_almacen_SKU = FormCambiarAlmacenPorSKU()
            form_fabricar = FormFabricar()
            form_crear_oc = FormCrearOC()
            form_actualizar_oc_ingredientes = FormActualizarMaxOCIngredientes()
            form_actualizar_oc_vacunas = FormActualizarMaxOCVacunas()
            ID_producto = request.POST.get('productoId', '')
            ID_almacen_externo = request.POST.get('almacenId_externo', '')
            ID_oc = request.POST.get('oc', '')
            precio = request.POST.get('precio', '')
            if form_cambiar_bodega.is_valid():
                post_valido = True
                if ID_almacen_externo not in ALMACENES_RECEPCION_EXT:
                    messages.warning(
                        request, '??El ID de este almac??n externo NO existe!')
                    post_valido = False
                if ID_producto not in IDs_productos:
                    messages.warning(
                        request, '??El ID de este producto NO existe!')
                    post_valido = False
                if post_valido:
                    mover_entre_bodegas(
                        {'productoId': ID_producto, "almacenId": ID_almacen_externo, "oc": ID_oc, "precio": precio})
                    messages.info(
                        request, '??El producto ha sido enviado a otra bodega!')
                    return HttpResponseRedirect('/backoffice')

        elif request.POST.get('SKU', '') != '' and request.POST.get('oc', '') == '' and request.POST.get('cantidad', '') == '':
            form_cambiar_almacen = FormCambiarAlmacen()
            form_cambiar_bodega = FormCambiarBodega()
            form_fabricar = FormFabricar()
            form_cambiar_almacen_SKU = FormCambiarAlmacenPorSKU(request.POST)
            almacen_origen = request.POST.get('almacen_origen', '')
            form_crear_oc = FormCrearOC()
            form_actualizar_oc_ingredientes = FormActualizarMaxOCIngredientes()
            form_actualizar_oc_vacunas = FormActualizarMaxOCVacunas()
            SKU = request.POST.get('SKU', '')
            ID_almacen = request.POST.get('almacenId', '')
            cant_SKU = int(request.POST.get('cant_SKU', ''))
            precio = request.POST.get('precio', '')
            if form_cambiar_almacen_SKU.is_valid():
                post_valido = True
                if ID_almacen not in IDs_almacenes:
                    messages.warning(
                        request, '??El ID de este almac??n NO existe!')
                    post_valido = False
                if SKU not in list(IDs_por_sku[almacen_origen].keys()):
                    messages.warning(
                        request, '??Este SKU NO existe en este almac??n!')
                    post_valido = False
                if post_valido:
                    print(IDs_por_sku)
                    for ID_producto in IDs_por_sku[almacen_origen][SKU][0:cant_SKU]:
                        print(ID_producto)
                        mover_entre_almacenes(
                            {'productoId': ID_producto, "almacenId": ID_almacen})
                    if cant_SKU > len(IDs_por_sku[almacen_origen][SKU]):
                        messages.info(
                            request, f'{len(IDs_por_sku[almacen_origen][SKU])} producto(s) han sido cambiado de almac??n')
                    else:
                        messages.info(
                            request, f'{cant_SKU} producto(s) han sido cambiado de almac??n')
                    return HttpResponseRedirect('/backoffice')

        elif request.POST.get('cantidad', '') != '' and request.POST.get('SKU', '') != '':
            valid_SKUs = [
                '100',
                '107',
                '108',
                '112',
                '113',
                '114',
                '118',
                '119',
                '129',
                '115',
                '120',
                '121',
                '126',
                '127',
                '132',
                '110',
                '103',
                '102',
                '1000',
                '1001',
                '10001',
                '10002',
                '10005' 
            ]
            form_cambiar_almacen = FormCambiarAlmacen()
            form_cambiar_bodega = FormCambiarBodega()
            form_fabricar = FormFabricar(request.POST)
            form_cambiar_almacen_SKU = FormCambiarAlmacenPorSKU()
            form_crear_oc = FormCrearOC()
            form_actualizar_oc_ingredientes = FormActualizarMaxOCIngredientes()
            form_actualizar_oc_vacunas = FormActualizarMaxOCVacunas()
            SKU = request.POST.get('SKU')
            cantidad = request.POST.get('cantidad')
            if form_fabricar.is_valid():
                post_valido = True
                if SKU not in valid_SKUs:
                    messages.warning(request, '??Este SKU NO existe!')
                    post_valido = False
                if post_valido:
                    response = fabricar_producto(
                        {"sku": SKU, "cantidad": cantidad})
                    data = response.json()
                    date = data['disponible']
                    messages.info(
                        request, f'Se han mandado a fabricar {cantidad} productos con sku {SKU}')
                    messages.info(
                        request, f"Su producto estara disponible el {date}")
                    return HttpResponseRedirect('/backoffice')

        
    else:
        form_cambiar_bodega = FormCambiarBodega()
        form_cambiar_almacen = FormCambiarAlmacen()
        form_cambiar_almacen_SKU = FormCambiarAlmacenPorSKU()
        form_fabricar = FormFabricar()
        form_crear_oc = FormCrearOC()
        form_actualizar_oc_ingredientes = FormActualizarMaxOCIngredientes()
        form_actualizar_oc_vacunas = FormActualizarMaxOCVacunas()
        
        # Si no existe el modelo lo creo previamente
        try: 
            max_ingredientes = CantidadMaxAceptada.objects.get(pk='ingredientes')
        #except CantidadMaxAceptada.DoesNotExist: 
        except:
            max_ingredientes = CantidadMaxAceptada(
                tipo_oc = 'ingredientes',
                cantidad = 10
            )
            max_ingredientes.save()
        # Si no existe el modelo lo creo previamente
        try: 
            max_vacunas = CantidadMaxAceptada.objects.get(pk='vacunas')
        # except CantidadMaxAceptada.DoesNotExist: 
        except:
            max_vacunas = CantidadMaxAceptada(
                tipo_oc = 'vacunas',
                cantidad = 10
            )
            max_vacunas.save()

    SKU_VACUNAS = ['10001','10002','10003','10004','10005','10006']

    ordenes_vacunas = EmbassyOC.objects.filter(
        estado="aceptada",
        sku__in=SKU_VACUNAS
    )
    aceptadas_vacunas = ordenes_vacunas.count()
    ordenes_ingredientes = RecievedOC.objects.filter(
        estado="aceptada",
    ).exclude(
        sku__in=SKU_VACUNAS
    )
    aceptadas_ingredientes = ordenes_ingredientes.count()

    max_vacunas = CantidadMaxAceptada.objects.get(pk='vacunas')
    max_ingredientes = CantidadMaxAceptada.objects.get(pk='ingredientes')

    return render(request, 'backoffice.html', {
        'almacenes': almacenes,
        'form_cambiar_almacen': form_cambiar_almacen,
        'form_cambiar_bodega': form_cambiar_bodega,
        'form_cambiar_almacen_SKU': form_cambiar_almacen_SKU,
        'form_fabricar': form_fabricar,
        'TITULO_ALM_EXT': TITULO_RECEPCIONES,
        'ALMACENES_EXTERNOS': ALMACENES_RECEPCION_EXT,
        'form_crear_oc': form_crear_oc,
        'ALMACENES_EXTERNOS': RECEPCIONES_DEV,
        'form_actualizar_oc_ingredientes': form_actualizar_oc_ingredientes,
        'form_actualizar_oc_vacunas': form_actualizar_oc_vacunas,
        'curr_max_vac': max_vacunas.cantidad,
        'curr_max_ing': max_ingredientes.cantidad,
        'aceptadas_vacunas': aceptadas_vacunas,
        'aceptadas_ingredientes': aceptadas_ingredientes})


def vacunas(request):

    if request.method == 'POST':
        tipo_vacuna = request.POST.get('tipo')
        fabricar_vacuna({ 'tipo': tipo_vacuna, 'cantidad': SKU_LOTE[tipo_vacuna] })

    form_fabricar_vacuna = FormCrearVacuna()

    # Informaci??n de los almacenes
    almacenes = obtener_almacenes().json()
    info_almacenes = {}
    for almacen in almacenes:
        id = almacen["_id"]
        used = almacen["usedSpace"]
        total = almacen["totalSpace"]
        if almacen["recepcion"]:
            info_almacenes['Recepci??n'] = [id, used, total]
        if almacen["despacho"]:
            info_almacenes['Despacho'] = [id, used, total]
        if almacen["pulmon"]:
            info_almacenes['Pulm??n'] = [id, used, total]
        if almacen["pulmon"] == False and almacen["despacho"] == False and almacen["recepcion"] == False:
            info_almacenes['Central'] = [id, used, total]
        almacen["almacenId"] = almacen["_id"]
    labels_almacenes = ['Recepci??n', 'Despacho', 'Pulm??n', 'Central']
    ocupacion_almacenes = [info_almacenes[i][1] for i in labels_almacenes]
    id_almacenes = [info_almacenes[i][0] for i in labels_almacenes]

    # Informaci??n stock disponible de vacunas y compuestos
    cantidad_sku = {}
    for almacen in almacenes:
        sku_almacen = obtener_stock(almacen).json()
        for sku in sku_almacen:
            if sku["_id"] in cantidad_sku:
                cantidad_sku[sku["_id"]] += int(sku["total"])
            else:
                cantidad_sku[sku["_id"]] = int(sku["total"])
    labels_stock = [key for key in cantidad_sku.keys()]
    stock = [cantidad_sku[i] for i in labels_stock]

    formulas = FORMULA

    map_keys = {
        '10005': "Moderna",
        '10002': "Sinovac",
        '10001': "Pfizer",
        '10003': 'Astrazeneca',
        '10004': 'Janssen',
        '10006': 'Sputnik'
    }
    names = [map_keys[key] for key in formulas.keys()]
    keys = [key for key in formulas.keys()]
    for key in keys:
        for ingrediente in formulas[key]:
            if ingrediente in labels_stock:
                FORMULA_COMPLETA[int(key)][int(ingrediente)]['Stock'] = cantidad_sku[ingrediente]
            else:
                FORMULA_COMPLETA[int(key)][int(ingrediente)]['Stock'] = 0
    return render(request, 'vacunas.html', {"formulas": formulas, "keys": keys, "map_keys": map_keys, "names": names, 'form_fabricar_vacuna': form_fabricar_vacuna, "formulas_completas": FORMULA_COMPLETA})
