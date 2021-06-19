from django.urls import include, path
from . import views

urlpatterns = [
    path('mipath/<str:algun_id>', views.algun_endopint, name='algun_endpoint'),
    path('stocks', views.consulta_stock, name='consulta_stock'),
    path('ordenes-compra/<str:id>', views.manejo_oc, name='manejo_oc'),
]