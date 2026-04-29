from django.urls import path
from . import views

urlpatterns = [
    path('registro/', views.registro,     name='registro'),
    path('login/',    views.login_view,   name='login'),
    path('logout/',   views.logout_view,  name='logout'),
    path('verificar-otp/', views.verificar_otp, name='verificar_otp'),
    path('consultar-cedula/',  views.consultar_cedula_ajax,  name='consultar_cedula_ajax'),
]