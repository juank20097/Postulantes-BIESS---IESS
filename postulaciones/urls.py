from django.urls import path
from . import views

urlpatterns = [
    path('paso/1/', views.paso_info_personal,       name='paso_info_personal'),
    path('paso/2/', views.paso_domicilio,            name='paso_domicilio'),
    path('paso/3/', views.paso_sector,               name='paso_sector'),
    path('paso/4/', views.paso_familiares,           name='paso_familiares'),
    path('paso/4/eliminar/<int:pk>/', views.eliminar_familiar, name='eliminar_familiar'),
    path('paso/5/eliminar/<int:pk>/', views.eliminar_formacion, name='eliminar_formacion'),
    path('paso/6/eliminar/<int:pk>/', views.eliminar_experiencia, name='eliminar_experiencia'),
    path('paso/7/eliminar-capacitacion/<int:pk>/', views.eliminar_capacitacion, name='eliminar_capacitacion'),
    path('paso/7/eliminar-publicacion/<int:pk>/',  views.eliminar_publicacion,  name='eliminar_publicacion'),
    path('admin-biess/',                    views.admin_postulaciones,        name='admin_postulaciones'),
    path('admin-biess/pdf/<int:pk>/', views.admin_pdf_postulante, name='admin_pdf_postulante'),
    path('admin-biess/estado/<int:pk>/',    views.admin_cambiar_estado,       name='admin_cambiar_estado'),
    path('admin-biess/excel/',              views.exportar_excel,             name='exportar_excel'),
    path('pdf/', views.descargar_pdf, name='descargar_pdf'),
    path('paso/5/', views.paso_formacion,            name='paso_formacion'),
    path('paso/6/', views.paso_experiencia,          name='paso_experiencia'),
    path('paso/7/', views.paso_capacitacion,         name='paso_capacitacion'),
    path('paso/8/', views.paso_inhabilidades,        name='paso_inhabilidades'),
    path('resumen/',      views.resumen_postulacion,      name='resumen_postulacion'),
    path('confirmacion/', views.confirmacion_postulacion, name='confirmacion_postulacion'),
]