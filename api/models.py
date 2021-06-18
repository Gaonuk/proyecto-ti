from django.db import models

# Create your models here.

class AlgunModelo(models.Model):
    id = models.CharField(primary_key=True, max_length=22)
    name = models.CharField(max_length=50)
    age = models.IntegerField()
