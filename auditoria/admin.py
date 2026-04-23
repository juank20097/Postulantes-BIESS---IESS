from django.contrib import admin
from .models import LogAccion, EstadoCambio, NotificacionEmail, SesionPostulante


@admin.register(LogAccion)
class LogAccionAdmin(admin.ModelAdmin):
    list_display  = ('timestamp', 'usuario', 'accion', 'modelo', 'objeto_id', 'ip')
    list_filter   = ('accion', 'modelo')
    search_fields = ('usuario__cedula', 'modelo')
    ordering      = ('-timestamp',)
    readonly_fields = ('timestamp',)


@admin.register(EstadoCambio)
class EstadoCambioAdmin(admin.ModelAdmin):
    list_display  = ('timestamp', 'postulante', 'estado_ant', 'estado_nvo', 'usuario')
    list_filter   = ('estado_nvo',)
    search_fields = ('postulante__cedula', 'postulante__codigo_unico')
    ordering      = ('-timestamp',)
    readonly_fields = ('timestamp',)


@admin.register(NotificacionEmail)
class NotificacionEmailAdmin(admin.ModelAdmin):
    list_display  = ('timestamp', 'tipo', 'destinatario', 'enviado', 'postulante')
    list_filter   = ('tipo', 'enviado')
    search_fields = ('destinatario', 'postulante__cedula')
    ordering      = ('-timestamp',)
    readonly_fields = ('timestamp',)


@admin.register(SesionPostulante)
class SesionPostulanteAdmin(admin.ModelAdmin):
    list_display  = ('usuario', 'ip', 'inicio', 'fin', 'activa')
    list_filter   = ('activa',)
    search_fields = ('usuario__cedula',)
    ordering      = ('-inicio',)
    readonly_fields = ('inicio',)