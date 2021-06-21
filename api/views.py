from django.shortcuts import render
from .serializers import AlgunSerializer # Ejemplo de Import
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.decorators import api_view
from django.http.response import JsonResponse
from rest_framework.response import Response
from .warehouse import despachar_producto, mover_entre_almacenes, mover_entre_bodegas, obtener_almacenes, obtener_productos_almacen, obtener_stock, fabricar_producto
from .OC import obtener_oc, recepcionar_oc, rechazar_oc
from .models import RecievedOC, SentOC
from datetime import datetime
from random import randint
import requests
import json

# Create your views here.

# Endpoints que exponemos para otros grupos

def parse_js_date(date):
    date_format = date[:-1]
    return datetime.fromisoformat(date_format)

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
            print(almacen['_id'])
            stock = obtener_stock(params).json()
            print(stock)
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

    else: # En caso de un method nada que ver
        return Response(
            {'message': f'{request.method} method not allowed for this request'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

@api_view(['POST', 'PATCH']) 
def manejo_oc(request, id):
    if request.method == 'POST':
        body = json.loads(request.body)

        if RecievedOC.objects.filter(id=id).exists():
            return Response({'message': 'OC ya fue recibida'},
            status=status.HTTP_400_BAD_REQUEST)
        else:
            orden_de_compra = obtener_oc(id).json()[0]
            oc = RecievedOC(id = id, cliente = orden_de_compra["cliente"], proveedor = orden_de_compra["cliente"],
            sku = orden_de_compra["sku"], fecha_entrega = parse_js_date(orden_de_compra["fechaEntrega"]), cantidad = orden_de_compra["cantidad"],
            cantidad_despachada = orden_de_compra["cantidadDespachada"], precio_unitario = orden_de_compra["precioUnitario"],
            canal = orden_de_compra["canal"], estado = orden_de_compra["estado"], created_at = parse_js_date(orden_de_compra["created_at"]),
            updated_at =  parse_js_date(orden_de_compra["updated_at"]))
            
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
            if randint(0,1) == 1:
                recepcionar_oc(id)
                requests.patch(url=url, params={"estado":"aceptada"})
            else:
                rechazar_oc(id, {"rechazo": "Rechazada por azar"})
                requests.patch(url=url, params={"estado":"rechazada"})

            response = {"id": id, "cliente": body["cliente"], "sku": body["sku"],"fechaEntrega": body["fechaEntrega"],
            "cantidad": body["cantidad"], "urlNotificacion": body["urlNotificacion"],"estado": "recibida"}

            return Response(response, status=status.HTTP_201_CREATED)


    elif request.method == 'PATCH':
        body = request.body
        estado = body["estado"]
        if SentOC.objects.filter(id=id).exists():
            sent_oc = SentOC.objects.get(id=id)
            sent_oc.update(estado=estado)
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)
    
    else: # En caso de un method nada que ver
        return Response(
            {'message': f'{request.method} method not allowed for this request'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )


@api_view(['GET', 'POST', 'DELETE', 'PUT']) # para que sirve esto
def algun_endopint(request, algun_id):
    # Si el URL que llama este endpoint tiene alguna variable,
    # debe ir en el input de la función, junto a request.
    if request.method == 'GET': #ejemplo para obtener todas las instancias de un modelo        artists = Artist.objects.all()
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
    elif request.method == 'PUT': #Ejemplo para reproducir las canciones de un album
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

    else: # En caso de un method nada que ver
        return Response(
            {'message': f'{request.method} method not allowed for this request'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

def index(request):

    ###Información de los almacenes
    almacenes = obtener_almacenes().json()
    info_almacenes = {}
    for almacen in almacenes: 
        id = almacen["_id"]
        used = almacen["usedSpace"]
        total = almacen["totalSpace"]
        if almacen["recepcion"]:
            info_almacenes['Recepción'] = [id,used,total]
        if almacen["despacho"]:
            info_almacenes['Despacho'] = [id,used,total]
        if almacen["pulmon"]:
            info_almacenes['Pulmón'] = [id,used,total]
        if almacen["pulmon"] == False and almacen["despacho"] == False and almacen["recepcion"] == False: 
            info_almacenes['Central'] = [id,used,total]
        almacen["almacenId"] = almacen["_id"]
    labels_almacenes = ['Recepción','Despacho','Pulmón','Central'] 
    ocupacion_almacenes = [info_almacenes[i][1] for i in labels_almacenes]
    id_almacenes = [info_almacenes[i][0] for i in labels_almacenes]
    
    ###Información stock disponible de vacunas y compuestos 
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

    return render(request, 'index.html',{'params':{'labels_almacenes': labels_almacenes, 'ocupacion_almacenes': ocupacion_almacenes, \
        'labels_stock': labels_stock, 'stock': stock }})