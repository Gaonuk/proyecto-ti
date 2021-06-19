from django.shortcuts import render
from .models import AlgunModelo # Ejemplo de Import
from .serializers import AlgunSerializer # Ejemplo de Import
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.decorators import api_view
from django.http.response import JsonResponse
from rest_framework.response import Response

# Create your views here.

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