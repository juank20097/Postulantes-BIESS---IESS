from django.urls import path
from . import views

urlpatterns = [
    path('registro/', views.registro,     name='registro'),
    path('login/',    views.login_view,   name='login'),
    path('logout/',   views.logout_view,  name='logout'),
    path('consultar-cedula/',  views.consultar_cedula_ajax,  name='consultar_cedula_ajax'),
]