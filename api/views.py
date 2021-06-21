from django.shortcuts import render
from requests.api import post
from .serializers import AlgunSerializer  # Ejemplo de Import
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.decorators import api_view
from django.http.response import JsonResponse
from rest_framework.response import Response
from .warehouse import despachar_producto, mover_entre_almacenes, mover_entre_bodegas, obtener_almacenes, obtener_productos_almacen, obtener_stock, fabricar_producto

from .forms import FormCambiarAlmacen, FormCambiarBodega, FormCambiarAlmacenPorSKU, FormFabricar
from django.http import HttpResponseRedirect
from django.contrib import messages

from .OC import obtener_oc, recepcionar_oc, rechazar_oc, parse_js_date
from .models import RecievedOC, SentOC
from random import randint
import requests
import json

# Create your views here.
from .arrays_almacenes_recep import RECEPCIONES_DEV, RECEPCIONES_PROD
import environ
import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
environ.Env.read_env(env_file= os.path.join(BASE_DIR, 'proyecto13/.env'))

# Endpoints que exponemos para otros grupos


if os.environ.get('DJANGO_DEVELOPMENT'):
    TITULO_RECEPCIONES = 'ALMACENES EXTERNOS DEV'
    ALMACENES_RECEPCION_EXT= RECEPCIONES_DEV
else:
    TITULO_RECEPCIONES = 'ALMACENES EXTERNOS PROD'
    ALMACENES_RECEPCION_EXT= RECEPCIONES_PROD




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


@api_view(['POST', 'PATCH'])
def manejo_oc(request, id):
    body = json.loads(request.body)
    if request.method == 'POST':

        if RecievedOC.objects.filter(id=id).exists():
            return Response({'message': 'OC ya fue recibida'},
                            status=status.HTTP_400_BAD_REQUEST)
        else:
            orden_de_compra = obtener_oc(id).json()[0]
            oc = RecievedOC(id=id, cliente=orden_de_compra["cliente"], proveedor=orden_de_compra["proveedor"],
                            sku=orden_de_compra["sku"], fecha_entrega=parse_js_date(orden_de_compra["fechaEntrega"]), cantidad=orden_de_compra["cantidad"],
                            cantidad_despachada=orden_de_compra[
                                "cantidadDespachada"], precio_unitario=orden_de_compra["precioUnitario"],
                            canal=orden_de_compra["canal"], estado=orden_de_compra["estado"], created_at=parse_js_date(
                                orden_de_compra["created_at"]),
                            updated_at=parse_js_date(orden_de_compra["updated_at"]))

            if "notas" in orden_de_compra.keys():
                oc.notas = orden_de_compra["notas"]
            if "rechazo" in orden_de_compra.keys():
                oc.rechazo = orden_de_compra["rechazo"]
            if "anulacion" in orden_de_compra.keys():
                oc.anulacion = orden_de_compra["anulacion"]
            if "urlNotificacion" in orden_de_compra.keys():
                oc.url_notificaion = orden_de_compra["urlNotificacion"]
            oc.save()
            url = orden_de_compra["urlNotificacion"]
            if randint(0, 1) == 1:
                recepcionar_oc(id)
                requests.patch(url=url, params={"estado": "aceptada"})
            else:
                rechazar_oc(id, {"rechazo": "Rechazada por azar"})
                requests.patch(url=url, params={"estado": "rechazada"})

            response = {"id": id, "cliente": body["cliente"], "sku": body["sku"], "fechaEntrega": body["fechaEntrega"],
                        "cantidad": body["cantidad"], "urlNotificacion": body["urlNotificacion"], "estado": "recibida"}

            return Response(response, status=status.HTTP_201_CREATED)

    elif request.method == 'PATCH':
        estado = body["estado"]
        if SentOC.objects.filter(id=id).exists():
            sent_oc = SentOC.objects.get(id=id)
            sent_oc.estado=estado
            sent_oc.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)

    else:  # En caso de un method nada que ver
        return Response(
            {'message': f'{request.method} method not allowed for this request'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )


@api_view(['GET', 'POST', 'DELETE', 'PUT'])  # para que sirve esto
def algun_endopint(request, algun_id):
    # Si el URL que llama este endpoint tiene alguna variable,
    # debe ir en el input de la función, junto a request.
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
        # Para un delete, generalmente querré borrar algo específico
        # por lo que necesitaría una variable del URL
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
    # Información de los almacenes
    almacenes = obtener_almacenes().json()
    info_almacenes = {}
    for almacen in almacenes:
        id = almacen["_id"]
        used = almacen["usedSpace"]
        total = almacen["totalSpace"]
        if almacen["recepcion"]:
            info_almacenes['Recepción'] = [id, used, total]
        if almacen["despacho"]:
            info_almacenes['Despacho'] = [id, used, total]
        if almacen["pulmon"]:
            info_almacenes['Pulmón'] = [id, used, total]
        if almacen["pulmon"] == False and almacen["despacho"] == False and almacen["recepcion"] == False:
            info_almacenes['Central'] = [id, used, total]
        almacen["almacenId"] = almacen["_id"]
    labels_almacenes = ['Recepción', 'Despacho', 'Pulmón', 'Central']
    ocupacion_almacenes = [info_almacenes[i][1] for i in labels_almacenes]
    id_almacenes = [info_almacenes[i][0] for i in labels_almacenes]

    # Información stock disponible de vacunas y compuestos
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

    orden_de_compra = obtener_oc("60d0ba39e72508000448529d").json()[0]
    oc = SentOC(id="60d0ba39e72508000448529d", cliente=orden_de_compra["cliente"], proveedor=orden_de_compra["proveedor"],
                    sku=orden_de_compra["sku"], fecha_entrega=parse_js_date(orden_de_compra["fechaEntrega"]), cantidad=orden_de_compra["cantidad"],
                    cantidad_despachada=orden_de_compra[
                        "cantidadDespachada"], precio_unitario=orden_de_compra["precioUnitario"],
                    canal=orden_de_compra["canal"], estado=orden_de_compra["estado"], created_at=parse_js_date(
                        orden_de_compra["created_at"]),
                    updated_at=parse_js_date(orden_de_compra["updated_at"]))

    if "notas" in orden_de_compra.keys():
        oc.notas = orden_de_compra["notas"]
    if "rechazo" in orden_de_compra.keys():
        oc.rechazo = orden_de_compra["rechazo"]
    if "anulacion" in orden_de_compra.keys():
        oc.anulacion = orden_de_compra["anulacion"]
    if "urlNotificacion" in orden_de_compra.keys():
        oc.url_notificaion = orden_de_compra["urlNotificacion"]
    oc.save()
            

    return render(request, 'index.html', {'params': {'labels_almacenes': labels_almacenes, 'ocupacion_almacenes': ocupacion_almacenes,
                                                     'labels_stock': labels_stock, 'stock': stock}})


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
        # Para cada almacén vemos su stock
        stock = obtener_stock(params).json()
        # Guardamos los IDs de los almacenes en un Array
        IDs_almacenes.append(almacen['_id'])
        # Guardamos en el mismo objeto los productos del almacen
        almacen['productos'] = stock
        # Guardamos la cantidad de productos del almacen para hacer un IF en el front
        almacen['cant_productos'] = len(stock)
        # Este array sirve para guardar por SKU todos los IDs de productos en el mismo objeto de almacén
        almacen['detalle_productos'] = {}
        print(stock)
        # Si hay productos en el almacen, iteramos sobre ellos
        IDs_por_sku[almacen['_id']] = {}
        if len(stock) > 0:
            for sku in stock:
                # Vamos a guardar en un objeto los SKUs y un array con sus IDs para ser usado en otro método
                IDs_por_sku[almacen['_id']][sku['_id']]= []
                # Sacamos todos los IDs por SKU
                productos_almacen = obtener_productos_almacen(
                    {"almacenId": almacen['_id'], "sku": sku["_id"]}).json()
                for producto_almacen in productos_almacen:
                    # Aquí se guardan todos los ID's por SKU y por almacen
                    IDs_por_sku[almacen['_id']][sku['_id']].append(producto_almacen['_id'])
                    # Creamos una nueva variable 'id' porque front no permite "_"
                    producto_almacen['id'] = producto_almacen['_id']
                    IDs_productos.append(producto_almacen["_id"])
                # Guardamos todos los productos según SKU en un objeto
                almacen['detalle_productos'][sku["_id"]] = productos_almacen
        

    if request.method == 'POST':
        # print(request.POST.get('cantidad'))
        # print(request.POST.get('SKU'))
        if request.POST.get('oc', '') == '' and request.POST.get('SKU', '') == '' and request.POST.get('cantidad', '') == '':
            form_cambiar_bodega = FormCambiarBodega()
            form_cambiar_almacen = FormCambiarAlmacen(request.POST)
            form_cambiar_almacen_SKU = FormCambiarAlmacenPorSKU()
            form_fabricar = FormFabricar()
            # print(IDs_almacenes)
            # print(IDs_productos)
            ID_producto = request.POST.get('productoId', '')
            ID_almacen = request.POST.get('almacenId', '')
            if form_cambiar_almacen.is_valid():
                post_valido = True
                if ID_almacen not in IDs_almacenes:
                    messages.warning(
                        request, '¡El ID de este almacén NO existe!')
                    post_valido = False
                if ID_producto not in IDs_productos:
                    messages.warning(
                        request, '¡El ID de este producto NO existe!')
                    post_valido = False
                if post_valido:
                    mover_entre_almacenes(
                        {'productoId': ID_producto, "almacenId": ID_almacen})
                    messages.info(
                        request, 'El producto ha sido cambiado de almacén')
                    return HttpResponseRedirect('/backoffice')
        elif request.POST.get('oc', '') != '' and request.POST.get('SKU', '') == '' and request.POST.get('cantidad', '') == '':
            form_cambiar_almacen = FormCambiarAlmacen()
            form_cambiar_bodega = FormCambiarBodega(request.POST)
            form_cambiar_almacen_SKU = FormCambiarAlmacenPorSKU()
            form_fabricar = FormFabricar()
            ID_producto = request.POST.get('productoId', '')
            ID_almacen_externo = request.POST.get('almacenId_externo', '')
            ID_oc = request.POST.get('oc', '')
            precio = request.POST.get('precio', '')
            if form_cambiar_bodega.is_valid():
                post_valido = True
                if ID_almacen_externo not in ALMACENES_RECEPCION_EXT:
                    messages.warning(
                        request, '¡El ID de este almacén externo NO existe!')
                    post_valido = False
                if ID_producto not in IDs_productos:
                    messages.warning(
                        request, '¡El ID de este producto NO existe!')
                    post_valido = False
                if post_valido:
                    mover_entre_bodegas(
                        {'productoId': ID_producto, "almacenId": ID_almacen_externo, "oc": ID_oc, "precio": precio})
                    messages.info(
                        request, '¡El producto ha sido enviado a otra bodega!')
                    return HttpResponseRedirect('/backoffice')

        elif request.POST.get('SKU', '') != '' and request.POST.get('oc', '') == '' and request.POST.get('cantidad', '') == '':
            form_cambiar_almacen = FormCambiarAlmacen()
            form_cambiar_bodega = FormCambiarBodega()
            form_fabricar = FormFabricar()
            form_cambiar_almacen_SKU = FormCambiarAlmacenPorSKU(request.POST)
            almacen_origen = request.POST.get('almacen_origen', '')
            SKU = request.POST.get('SKU', '')
            ID_almacen = request.POST.get('almacenId', '')
            cant_SKU = int(request.POST.get('cant_SKU', ''))
            precio = request.POST.get('precio', '')
            if form_cambiar_almacen_SKU.is_valid():
                post_valido = True
                if ID_almacen not in IDs_almacenes:
                    messages.warning(
                        request, '¡El ID de este almacén NO existe!')
                    post_valido = False
                if SKU not in list(IDs_por_sku[almacen_origen].keys()):
                    messages.warning(request, '¡Este SKU NO existe en este almacén!')
                    post_valido = False
                if post_valido:
                    print(IDs_por_sku)
                    for ID_producto in IDs_por_sku[almacen_origen][SKU][0:cant_SKU]:
                        print(ID_producto)
                        mover_entre_almacenes(
                            {'productoId': ID_producto, "almacenId": ID_almacen})
                    if cant_SKU > len(IDs_por_sku[almacen_origen][SKU]):
                        messages.info(
                            request, f'{len(IDs_por_sku[almacen_origen][SKU])} producto(s) han sido cambiado de almacén')
                    else:
                        messages.info(
                            request, f'{cant_SKU} producto(s) han sido cambiado de almacén')
                    return HttpResponseRedirect('/backoffice')

        elif request.POST.get('cantidad') != '' and request.POST.get('SKU') != '':
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
                '1000',
                '10001',
                '30001',
                '30002',
                '30003',
                '30004',
                '30005',
                '30006',
                '30007',
                '30008',
                '30009',
                '30010',
                '30011',
                '30012',
                '30013',
                '30014',
                '30015',
                '30016',
                '30017',
                '30018',
                '30019',
                '30020',
                '30021',
                '30022',
                '30023',
                '30024'
            ]
            form_cambiar_almacen = FormCambiarAlmacen()
            form_cambiar_bodega = FormCambiarBodega()
            form_fabricar = FormFabricar(request.POST)
            form_cambiar_almacen_SKU = FormCambiarAlmacenPorSKU()
            SKU = request.POST.get('SKU')
            cantidad = request.POST.get('cantidad')
            if form_fabricar.is_valid():
                post_valido = True
                if SKU not in valid_SKUs:
                    messages.warning(request, '¡Este SKU NO existe!')
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

    # print(almacenes)
    return render(request, 'backoffice.html', {
        'almacenes': almacenes,
        'form_cambiar_almacen': form_cambiar_almacen,
        'form_cambiar_bodega': form_cambiar_bodega,
        'form_cambiar_almacen_SKU': form_cambiar_almacen_SKU,
        'form_fabricar': form_fabricar,
        'TITULO_ALM_EXT': TITULO_RECEPCIONES,
        'ALMACENES_EXTERNOS': ALMACENES_RECEPCION_EXT})
