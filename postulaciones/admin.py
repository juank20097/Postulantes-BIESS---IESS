from django.contrib import admin
from .models import (
    Postulante, FamiliarIESS, FormacionAcademica,
    ExperienciaProfesional, Capacitacion, Publicacion, Inhabilidades
)


class FamiliarInline(admin.TabularInline):
    model  = FamiliarIESS
    extra  = 0


class FormacionInline(admin.TabularInline):
    model  = FormacionAcademica
    extra  = 0


class ExperienciaInline(admin.TabularInline):
    model  = ExperienciaProfesional
    extra  = 0


class CapacitacionInline(admin.TabularInline):
    model  = Capacitacion
    extra  = 0


class PublicacionInline(admin.TabularInline):
    model  = Publicacion
    extra  = 0


class InhabilidadesInline(admin.StackedInline):
    model  = Inhabilidades
    extra  = 0


@admin.register(Postulante)
class PostulanteAdmin(admin.ModelAdmin):
    list_display   = ('codigo_unico', 'apellidos', 'nombres', 'cedula', 'sector', 'estado', 'creado_en')
    list_filter    = ('sector', 'estado')
    search_fields  = ('cedula', 'nombres', 'apellidos', 'codigo_unico')
    ordering       = ('-creado_en',)
    readonly_fields = ('codigo_unico', 'creado_en', 'modificado')
    inlines = [
        FamiliarInline,
        FormacionInline,
        ExperienciaInline,
        CapacitacionInline,
        PublicacionInline,
        InhabilidadesInline,
    ]
    fieldsets = (
        ('Identificación', {
            'fields': ('usuario', 'codigo_unico', 'sector', 'estado')
        }),
        ('Información personal', {
            'fields': (
                'nombres', 'apellidos', 'cedula', 'genero',
                'fecha_nacimiento', 'nacionalidad', 'estado_civil',
                'conyuge_nombres', 'conyuge_cedula',
            )
        }),
        ('Domicilio y contacto', {
            'fields': (
                'pais', 'provincia', 'ciudad',
                'calle_principal', 'numero', 'calle_secundaria',
                'sector_domicilio', 'referencia',
                'telefono_celular', 'telefono_domicilio', 'email_secundario',
            )
        }),
        ('Organización de respaldo', {
            'fields': ('tiene_organizacion', 'nombre_organizacion', 'doc_organizacion')
        }),
        ('Timestamps', {
            'fields': ('creado_en', 'modificado'),
            'classes': ('collapse',)
        }),
    )


@admin.register(FamiliarIESS)
class FamiliarIESSAdmin(admin.ModelAdmin):
    list_display  = ('nombres', 'parentesco', 'institucion', 'area', 'cargo', 'postulante')
    search_fields = ('nombres', 'postulante__cedula')
    list_filter   = ('institucion', 'parentesco')


@admin.register(FormacionAcademica)
class FormacionAcademicaAdmin(admin.ModelAdmin):
    list_display  = ('titulo', 'nivel', 'tipo', 'area_estudios', 'fecha_senescyt', 'postulante')
    search_fields = ('titulo', 'postulante__cedula')
    list_filter   = ('nivel', 'tipo', 'area_estudios')


@admin.register(ExperienciaProfesional)
class ExperienciaProfesionalAdmin(admin.ModelAdmin):
    list_display  = ('cargo', 'institucion', 'tipo', 'fecha_inicio', 'fecha_fin', 'postulante')
    search_fields = ('cargo', 'institucion', 'postulante__cedula')
    list_filter   = ('tipo', 'actividades_area')


@admin.register(Capacitacion)
class CapacitacionAdmin(admin.ModelAdmin):
    list_display  = ('nombre', 'tipo_evento', 'institucion', 'horas', 'fecha_inicio', 'postulante')
    search_fields = ('nombre', 'postulante__cedula')
    list_filter   = ('tipo_evento',)


@admin.register(Publicacion)
class PublicacionAdmin(admin.ModelAdmin):
    list_display  = ('titulo', 'tipo', 'medio', 'fecha', 'relacionado', 'postulante')
    search_fields = ('titulo', 'postulante__cedula')
    list_filter   = ('tipo', 'relacionado')


@admin.register(Inhabilidades)
class InhabilidadesAdmin(admin.ModelAdmin):
    list_display  = ('postulante', 'p1_goce_derechos', 'p5_funcionario_iess', 'p7_removido_organismo')
    search_fields = ('postulante__cedula',)