from django.shortcuts import render
from .models import AlgunModelo # Ejemplo de Import
from .serializers import AlgunSerializer # Ejemplo de Import
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.decorators import api_view
from django.http.response import JsonResponse
from rest_framework.response import Response
from .warehouse import despachar_producto, mover_entre_almacenes, mover_entre_bodegas, obtener_almacenes, obtener_productos_almacen, obtener_stock, fabricar_producto

# Create your views here.

# Endpoints que exponemos para otros grupos

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
        pass

    elif request.method == 'PATCH':
        pass
    
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