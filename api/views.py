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
from .arrays_almacenes_recep import RECEPCIONES_DEV,RECEPCIONES_PROD
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

    return render(request, 'index.html',{'params':{'param_1':'Param 1 pasado desde el backend','param_2':'Param 2 pasado desde el backend'}})

from .forms import FormCambiarAlmacen,FormCambiarBodega,FormCambiarAlmacenPorSKU
from django.http import HttpResponseRedirect
from django.contrib import messages

def backoffice(request):
    #Arrays para hacer comparativas
    #antes de enviar el POST
    IDs_almacenes=[]
    IDs_productos=[]
    IDs_por_sku={}
    #Obtenemos todos los almacenes 
    almacenes = obtener_almacenes().json()
    for almacen in almacenes:
        #Creamos una nueva variable 'id' porque front no permite "_"
        almacen['id']=almacen['_id']
        params = {'almacenId': almacen['_id']}
        #Para cada almacén vemos su stock
        stock = obtener_stock(params).json()
        #Guardamos los IDs de los almacenes en un Array
        IDs_almacenes.append(almacen['_id'])
        #Guardamos en el mismo objeto los productos del almacen
        almacen['productos'] = stock
        #Guardamos la cantidad de productos del almacen para hacer un IF en el front
        almacen['cant_productos'] = len(stock)
        #Este array sirve para guardar por SKU todos los IDs de productos en el mismo objeto de almacén
        almacen['detalle_productos']={}
        print(stock)
        #Si hay productos en el almacen, iteramos sobre ellos
        if len(stock)>0:
            for sku in stock:
                #Vamos a guardar en un objeto los SKUs y un array con sus IDs para ser usado en otro método
                IDs_por_sku[sku['_id']]= []
                #Sacamos todos los IDs por SKU
                productos_almacen = obtener_productos_almacen({"almacenId":almacen['_id'], "sku": sku["_id"] }).json()
                for producto_almacen in productos_almacen:
                    #Aquí se guardan todos los ID's por SKU
                    IDs_por_sku[sku['_id']].append(producto_almacen['_id'])
                    #Creamos una nueva variable 'id' porque front no permite "_"
                    producto_almacen['id'] = producto_almacen['_id']
                    IDs_productos.append(producto_almacen["_id"])
                #Guardamos todos los productos según SKU en un objeto 
                almacen['detalle_productos'][sku["_id"]] = productos_almacen
                    

    if request.method == 'POST':
        if request.POST.get('oc','')=='' and request.POST.get('SKU','')=='':
            form_cambiar_bodega = FormCambiarBodega()
            form_cambiar_almacen = FormCambiarAlmacen(request.POST)
            form_cambiar_almacen_SKU = FormCambiarAlmacenPorSKU()
            # print(IDs_almacenes)
            # print(IDs_productos)
            ID_producto = request.POST.get('productoId','')
            ID_almacen = request.POST.get('almacenId','')
            if form_cambiar_almacen.is_valid():
                post_valido = True
                if ID_almacen not in IDs_almacenes:
                    messages.warning(request, '¡El ID de este almacén NO existe!')
                    post_valido = False
                if ID_producto not in IDs_productos:
                    messages.warning(request, '¡El ID de este producto NO existe!')
                    post_valido = False
                if post_valido:
                    mover_entre_almacenes({'productoId': ID_producto, "almacenId": ID_almacen })
                    messages.info(request, 'El producto ha sido cambiado de almacén')
                    return HttpResponseRedirect('/backoffice')    
        elif request.POST.get('oc','')!='' and request.POST.get('SKU','')=='':
            form_cambiar_almacen = FormCambiarAlmacen()
            form_cambiar_bodega = FormCambiarBodega(request.POST)
            form_cambiar_almacen_SKU = FormCambiarAlmacenPorSKU()
            ID_producto = request.POST.get('productoId','')
            ID_almacen_externo = request.POST.get('almacenId_externo','')
            ID_oc = request.POST.get('oc','')
            precio = request.POST.get('precio','')
            if form_cambiar_bodega.is_valid():
                post_valido = True
                if ID_almacen_externo not in RECEPCIONES_DEV:
                    messages.warning(request, '¡El ID de este almacén externo NO existe!')
                    post_valido = False
                if ID_producto not in IDs_productos:
                    messages.warning(request, '¡El ID de este producto NO existe!')
                    post_valido = False
                if post_valido:
                    mover_entre_bodegas({'productoId': ID_producto, "almacenId": ID_almacen_externo, "oc":ID_oc, "precio": precio })
                    messages.info(request, '¡El producto ha sido enviado a otra bodega!')
                    return HttpResponseRedirect('/backoffice')

        elif request.POST.get('SKU','')!='' and request.POST.get('oc','')=='':
            form_cambiar_almacen = FormCambiarAlmacen()
            form_cambiar_bodega = FormCambiarBodega()
            form_cambiar_almacen_SKU = FormCambiarAlmacenPorSKU(request.POST)
            SKU = request.POST.get('SKU','')
            ID_almacen = request.POST.get('almacenId','')
            precio = request.POST.get('precio','')
            if form_cambiar_almacen_SKU.is_valid():
                post_valido = True
                if ID_almacen not in IDs_almacenes:
                    messages.warning(request, '¡El ID de este almacén NO existe!')
                    post_valido = False
                if SKU not in list(IDs_por_sku.keys()):
                    messages.warning(request, '¡Este SKU NO existe!')
                    post_valido = False
                if post_valido:
                    for ID_producto in IDs_por_sku[SKU]:
                        mover_entre_almacenes({'productoId': ID_producto, "almacenId": ID_almacen })
                    messages.info(request, f'{len(IDs_por_sku[SKU])} producto(s) han sido cambiado de almacén')

    else:
        form_cambiar_bodega = FormCambiarBodega()
        form_cambiar_almacen = FormCambiarAlmacen()
        form_cambiar_almacen_SKU= FormCambiarAlmacenPorSKU()





    # print(almacenes)
    return render(request, 'backoffice.html',{
        'almacenes':almacenes, 
        'form_cambiar_almacen': form_cambiar_almacen, 
        'form_cambiar_bodega':form_cambiar_bodega, 
        'form_cambiar_almacen_SKU':form_cambiar_almacen_SKU,
        'ALMACENES_EXTERNOS': RECEPCIONES_DEV})