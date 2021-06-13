from rest_framework import serializers
from .models import Artist, Album, Track

class AlgunSerializer(serializers.ModelSerializer):

    class Meta:
        model = AlgunModelo
        fields = [
            'id',
            'name',
            'age',
        ]