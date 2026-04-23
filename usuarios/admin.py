from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import PostulanteUser, RegistroCI, TokenActivacion, RecuperacionPassword


@admin.register(PostulanteUser)
class PostulanteUserAdmin(UserAdmin):
    list_display   = ('cedula', 'email', 'is_active', 'is_staff', 'fecha_reg')
    list_filter    = ('is_active', 'is_staff')
    search_fields  = ('cedula', 'email')
    ordering       = ('-fecha_reg',)
    fieldsets = (
        (None,       {'fields': ('cedula', 'email', 'password')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas',   {'fields': ('last_login', 'fecha_reg')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields':  ('cedula', 'email', 'password1', 'password2', 'is_active', 'is_staff'),
        }),
    )
    readonly_fields = ('fecha_reg', 'last_login')


@admin.register(RegistroCI)
class RegistroCIAdmin(admin.ModelAdmin):
    list_display  = ('cedula', 'intentos', 'bloqueado_hasta', 'actualizado_en')
    search_fields = ('cedula',)


@admin.register(TokenActivacion)
class TokenActivacionAdmin(admin.ModelAdmin):
    list_display  = ('usuario', 'token', 'expira', 'usado', 'creado_en')
    list_filter   = ('usado',)
    search_fields = ('usuario__cedula',)


@admin.register(RecuperacionPassword)
class RecuperacionPasswordAdmin(admin.ModelAdmin):
    list_display  = ('usuario', 'token', 'expira', 'usado', 'creado_en')
    list_filter   = ('usado',)
    search_fields = ('usuario__cedula',)