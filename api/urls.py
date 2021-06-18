from django.urls import include, path
from . import views

urlpatterns = [
    path('mipath/<str:algun_id>', views.algun_endopint, name='algun_endpoint'),
]