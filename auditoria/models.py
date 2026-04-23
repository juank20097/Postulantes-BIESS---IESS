from django.db import models


class LogAccion(models.Model):
    """
    Trazabilidad completa y auditable de todas las acciones.
    EF-12 / EF-13: requerido por organismos de control.
    """
    ACCION_CHOICES = [
        ('REGISTRO',         'Registro de usuario'),
        ('LOGIN',            'Inicio de sesión'),
        ('LOGOUT',           'Cierre de sesión'),
        ('GUARDAR_PROGRESO', 'Guardar progreso formulario'),
        ('ENVIAR_POSTULACION','Envío de postulación'),
        ('EDITAR_SECCION',   'Edición de sección'),
        ('ELIMINAR_ITEM',    'Eliminación de ítem'),
        ('SUBIR_DOCUMENTO',  'Subida de documento PDF'),
        ('CAMBIO_ESTADO',    'Cambio de estado'),
        ('ADMIN_ACCION',     'Acción de administrador'),
    ]

    usuario    = models.ForeignKey(
        'usuarios.PostulanteUser',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='logs'
    )
    accion     = models.CharField(max_length=25, choices=ACCION_CHOICES)
    modelo     = models.CharField(max_length=50, blank=True)
    objeto_id  = models.IntegerField(null=True, blank=True)
    detalle    = models.JSONField(default=dict)
    ip         = models.GenericIPAddressField(null=True, blank=True)
    timestamp  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Log de acción'
        verbose_name_plural = 'Logs de acciones'
        ordering            = ['-timestamp']

    def __str__(self):
        return f'[{self.timestamp:%Y-%m-%d %H:%M}] {self.get_accion_display()} — {self.modelo}'


class EstadoCambio(models.Model):
    """
    Historial de todos los cambios de estado de cada postulación.
    Requerido para auditoría de organismos de control (EF-13).
    """
    postulante  = models.ForeignKey(
        'postulaciones.Postulante',
        on_delete=models.CASCADE,
        related_name='cambios_estado'
    )
    estado_ant  = models.CharField(max_length=15)
    estado_nvo  = models.CharField(max_length=15)
    usuario     = models.ForeignKey(
        'usuarios.PostulanteUser',
        null=True, blank=True,
        on_delete=models.SET_NULL
    )
    observacion = models.TextField(blank=True)
    timestamp   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Cambio de estado'
        verbose_name_plural = 'Cambios de estado'
        ordering            = ['-timestamp']

    def __str__(self):
        return f'{self.postulante} : {self.estado_ant} → {self.estado_nvo}'


class NotificacionEmail(models.Model):
    """
    Registro de todos los correos enviados.
    EF-12 1.10.3 / Especificaciones suplementarias:
    estimado 10.000 correos durante todo el proceso.
    """
    TIPO_CHOICES = [
        ('ACTIVACION',      'Activación de cuenta'),
        ('RECUPERACION',    'Recuperación de contraseña'),
        ('CONFIRMACION',    'Confirmación de postulación'),
        ('RESULTADO_ETAPA', 'Resultado de etapa'),
        ('HABILITADO',      'Postulante habilitado'),
        ('INHABILITADO',    'Postulante inhabilitado'),
        ('EVALUACION',      'Acceso a evaluación técnica'),
        ('CALIFICACION',    'Notificación de calificación'),
    ]

    postulante   = models.ForeignKey(
        'postulaciones.Postulante',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='notificaciones'
    )
    tipo         = models.CharField(max_length=20, choices=TIPO_CHOICES)
    destinatario = models.EmailField()
    asunto       = models.CharField(max_length=200, blank=True)
    enviado      = models.BooleanField(default=False)
    error        = models.TextField(blank=True)
    timestamp    = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Notificación email'
        verbose_name_plural = 'Notificaciones email'
        ordering            = ['-timestamp']

    def __str__(self):
        estado = '✓' if self.enviado else '✗'
        return f'{estado} {self.get_tipo_display()} → {self.destinatario}'


class SesionPostulante(models.Model):
    """
    EF-11: registro de sesiones activas.
    Especificaciones suplementarias: tiempo máximo de sesión 30 minutos.
    """
    usuario    = models.ForeignKey(
        'usuarios.PostulanteUser',
        on_delete=models.CASCADE,
        related_name='sesiones'
    )
    ip         = models.GenericIPAddressField(null=True, blank=True)
    inicio     = models.DateTimeField(auto_now_add=True)
    fin        = models.DateTimeField(null=True, blank=True)
    activa     = models.BooleanField(default=True)

    class Meta:
        verbose_name        = 'Sesión de postulante'
        verbose_name_plural = 'Sesiones de postulantes'
        ordering            = ['-inicio']

    def __str__(self):
        estado = 'activa' if self.activa else 'cerrada'
        return f'{self.usuario.cedula} — {self.inicio:%Y-%m-%d %H:%M} ({estado})'