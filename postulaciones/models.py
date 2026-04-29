from django.db import models
from django.core.exceptions import ValidationError
import uuid


def validar_pdf(archivo):
    if not archivo.name.lower().endswith('.pdf'):
        raise ValidationError('Solo se permiten archivos PDF.')


# ── Helpers de upload_to ──────────────────────────────────────────────────────

def _carpeta_usuario(postulante):
    """
    Devuelve la carpeta raíz del usuario dentro del bucket:
    BIESS-XXXXXXXX_1234567890
    """
    cedula = postulante.usuario.cedula if postulante.usuario_id else 'sin_cedula'
    codigo = postulante.codigo_unico or 'NUEVO'
    return f'{codigo}_{cedula}'


def upload_organizacion(instance, filename):
    """BIESS-XXXX_cedula/organizaciones/organizacion_cedula.pdf"""
    cedula  = instance.usuario.cedula
    carpeta = _carpeta_usuario(instance)
    ext     = filename.rsplit('.', 1)[-1].lower()
    return f'{carpeta}/organizaciones/organizacion_{cedula}.{ext}'


def upload_formacion(instance, filename):
    """BIESS-XXXX_cedula/formacion/formacion_cedula_titulo.pdf"""
    cedula  = instance.postulante.usuario.cedula
    carpeta = _carpeta_usuario(instance.postulante)
    titulo  = instance.titulo[:40].replace(' ', '_').lower() if instance.titulo else 'doc'
    ext     = filename.rsplit('.', 1)[-1].lower()
    return f'{carpeta}/formacion/formacion_{cedula}_{titulo}.{ext}'


def upload_experiencia(instance, filename):
    """BIESS-XXXX_cedula/experiencia/experiencia_cedula_cargo.pdf"""
    cedula  = instance.postulante.usuario.cedula
    carpeta = _carpeta_usuario(instance.postulante)
    cargo   = instance.cargo[:40].replace(' ', '_').lower() if instance.cargo else 'doc'
    ext     = filename.rsplit('.', 1)[-1].lower()
    return f'{carpeta}/experiencia/experiencia_{cedula}_{cargo}.{ext}'


def upload_capacitacion(instance, filename):
    """BIESS-XXXX_cedula/capacitacion/capacitacion_cedula_nombre.pdf"""
    cedula  = instance.postulante.usuario.cedula
    carpeta = _carpeta_usuario(instance.postulante)
    nombre  = instance.nombre[:40].replace(' ', '_').lower() if instance.nombre else 'doc'
    ext     = filename.rsplit('.', 1)[-1].lower()
    return f'{carpeta}/capacitacion/capacitacion_{cedula}_{nombre}.{ext}'


def upload_publicacion(instance, filename):
    """BIESS-XXXX_cedula/publicaciones/publicacion_cedula_titulo.pdf"""
    cedula  = instance.postulante.usuario.cedula
    carpeta = _carpeta_usuario(instance.postulante)
    titulo  = instance.titulo[:40].replace(' ', '_').lower() if instance.titulo else 'doc'
    ext     = filename.rsplit('.', 1)[-1].lower()
    return f'{carpeta}/publicaciones/publicacion_{cedula}_{titulo}.{ext}'


# ─────────────────────────────────────────────────────────────────────────────


class Postulante(models.Model):
    """
    Modelo central del formulario BIESS.
    EF-12: agrupa toda la información del postulante
    separada en secciones según el RF.
    """

    SECTOR_CHOICES = [
        ('AFILIADO',  'Miembro Principal y Alterno — Sector Afiliados'),
        ('JUBILADO',  'Miembro Principal y Alterno — Sector Jubilados'),
        ('EMPLEADOR', 'Miembro Principal y Alterno — Sector Empleador'),
    ]
    ESTADO_CHOICES = [
        ('BORRADOR',     'Borrador'),
        ('ENVIADO',      'Enviado'),
        ('EN_REVISION',  'En revisión'),
        ('HABILITADO',   'Habilitado'),
        ('INHABILITADO', 'Inhabilitado'),
        ('FASE_MERITOS', 'Fase de méritos'),
        ('EVAL_TECNICA', 'Evaluación técnica'),
        ('FINALIZADO',   'Finalizado'),
    ]
    ESTADO_CIVIL_CHOICES = [
        ('SOLTERO',     'Soltero/a'),
        ('CASADO',      'Casado/a'),
        ('DIVORCIADO',  'Divorciado/a'),
        ('VIUDO',       'Viudo/a'),
        ('UNION_HECHO', 'Unión de hecho'),
    ]
    GENERO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
    ]

    usuario      = models.OneToOneField(
        'usuarios.PostulanteUser',
        on_delete=models.CASCADE,
        related_name='postulante'
    )
    codigo_unico = models.CharField(max_length=20, unique=True, blank=True)
    sector       = models.CharField(max_length=15, choices=SECTOR_CHOICES, blank=True)
    estado       = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='BORRADOR')

    nombres          = models.CharField(max_length=100, blank=True)
    apellidos        = models.CharField(max_length=100, blank=True)
    cedula           = models.CharField(max_length=10, blank=True)
    genero           = models.CharField(max_length=1, choices=GENERO_CHOICES, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    nacionalidad     = models.CharField(max_length=60, blank=True)
    estado_civil     = models.CharField(max_length=15, choices=ESTADO_CIVIL_CHOICES, blank=True)
    conyuge_nombres  = models.CharField(max_length=100, blank=True)
    conyuge_cedula   = models.CharField(max_length=10, blank=True)

    pais               = models.CharField(max_length=80, blank=True)
    provincia          = models.CharField(max_length=80, blank=True)
    ciudad             = models.CharField(max_length=80, blank=True)
    calle_principal    = models.CharField(max_length=150, blank=True)
    numero             = models.CharField(max_length=15, blank=True)
    calle_secundaria   = models.CharField(max_length=150, blank=True)
    sector_domicilio   = models.CharField(max_length=100, blank=True)
    referencia         = models.CharField(max_length=250, blank=True)
    telefono_celular   = models.CharField(max_length=15, blank=True)
    telefono_domicilio = models.CharField(max_length=15, blank=True)
    email_secundario   = models.EmailField(blank=True)

    tiene_organizacion  = models.BooleanField(null=True, blank=True)
    nombre_organizacion = models.CharField(max_length=200, blank=True)
    doc_organizacion    = models.FileField(
        upload_to=upload_organizacion,
        null=True, blank=True,
        validators=[validar_pdf]
    )

    creado_en  = models.DateTimeField(auto_now_add=True)
    modificado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Postulante'
        verbose_name_plural = 'Postulantes'

    def save(self, *args, **kwargs):
        if not self.codigo_unico:
            self.codigo_unico = f'BIESS-{str(uuid.uuid4())[:8].upper()}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.codigo_unico} — {self.apellidos} {self.nombres}'


class FamiliarIESS(models.Model):
    """
    EF-12 sección 1.3: familiares dentro del segundo grado
    de consanguinidad y cuarto de afinidad trabajando en IESS/BIESS.
    """
    PARENTESCO_CHOICES = [
        ('CONYUGE',       'Cónyuge'),
        ('CONVIVIENTE',   'Conviviente'),
        ('HIJO',          'Hijo/a'),
        ('PADRE',         'Padre'),
        ('MADRE',         'Madre'),
        ('HERMANO',       'Hermano/a'),
        ('CUÑADO',        'Cuñado/a'),
        ('SUEGRO',        'Suegro/a'),
        ('YERNO',         'Yerno'),
        ('NUERA',         'Nuera'),
        ('NIETO',         'Nieto/a'),
        ('TIO',           'Tío/a'),
        ('SOBRINO',       'Sobrino/a'),
        ('PRIMO_HERMANO', 'Primo hermano/a'),
        ('HIJO_POLITICO', 'Hijo político'),
    ]
    INSTITUCION_CHOICES = [
        ('IESS',  'IESS'),
        ('BIESS', 'BIESS'),
    ]

    postulante  = models.ForeignKey(
        Postulante, on_delete=models.CASCADE, related_name='familiares'
    )
    nombres     = models.CharField(max_length=100)
    parentesco  = models.CharField(max_length=20, choices=PARENTESCO_CHOICES)
    institucion = models.CharField(max_length=5,  choices=INSTITUCION_CHOICES)
    area        = models.CharField(max_length=100)
    cargo       = models.CharField(max_length=100)

    class Meta:
        verbose_name        = 'Familiar en IESS/BIESS'
        verbose_name_plural = 'Familiares en IESS/BIESS'

    def __str__(self):
        return f'{self.nombres} ({self.get_parentesco_display()}) — {self.institucion}'


class FormacionAcademica(models.Model):
    """
    EF-12 sección 1.5: formación académica del postulante.
    """
    NIVEL_CHOICES = [
        ('TERCER',   'Tercer nivel de grado'),
        ('ESP',      'Cuarto nivel — Especialidad académica'),
        ('MAESTRIA', 'Cuarto nivel — Maestría académica'),
        ('PHD',      'Cuarto nivel PhD — Doctorado'),
    ]
    TIPO_CHOICES = [
        ('NACIONAL',   'Nacional'),
        ('EXTRANJERA', 'Extranjera'),
    ]
    AREA_CHOICES = [
        ('FINANZAS',    'Finanzas'),
        ('MERCADO_CAP', 'Mercado de capitales'),
        ('ADMIN',       'Administración de empresas'),
        ('ECONOMIA',    'Economía'),
        ('DERECHO',     'Derecho'),
        ('AFINES',      'Materias afines'),
    ]

    postulante     = models.ForeignKey(
        Postulante, on_delete=models.CASCADE, related_name='formaciones'
    )
    nivel          = models.CharField(max_length=10, choices=NIVEL_CHOICES)
    institucion    = models.CharField(max_length=200)
    tipo           = models.CharField(max_length=10, choices=TIPO_CHOICES)
    titulo         = models.CharField(max_length=200)
    area_estudios  = models.CharField(max_length=15, choices=AREA_CHOICES)
    num_senescyt   = models.CharField(max_length=50)
    fecha_senescyt = models.DateField()
    documento      = models.FileField(
        upload_to=upload_formacion,
        validators=[validar_pdf]
    )

    class Meta:
        verbose_name        = 'Formación académica'
        verbose_name_plural = 'Formaciones académicas'
        ordering            = ['-fecha_senescyt']

    def __str__(self):
        return f'{self.titulo} — {self.postulante.codigo_unico}'


class ExperienciaProfesional(models.Model):
    """
    EF-12 sección 1.6: experiencia profesional.
    """
    TIPO_CHOICES = [
        ('GENERAL',   'General'),
        ('DIRECCION', 'Dirección'),
    ]
    AREA_CHOICES = FormacionAcademica.AREA_CHOICES

    postulante       = models.ForeignKey(
        Postulante, on_delete=models.CASCADE, related_name='experiencias'
    )
    tipo             = models.CharField(max_length=10, choices=TIPO_CHOICES)
    cargo            = models.CharField(max_length=150)
    institucion      = models.CharField(max_length=200)
    fecha_inicio     = models.DateField()
    fecha_fin        = models.DateField()
    actividades_area = models.CharField(max_length=15, choices=AREA_CHOICES)
    descripcion      = models.TextField(max_length=1000)
    documento        = models.FileField(
        upload_to=upload_experiencia,
        validators=[validar_pdf]
    )

    class Meta:
        verbose_name        = 'Experiencia profesional'
        verbose_name_plural = 'Experiencias profesionales'
        ordering            = ['-fecha_inicio']

    @property
    def tiempo_calculado(self):
        from dateutil.relativedelta import relativedelta
        delta = relativedelta(self.fecha_fin, self.fecha_inicio)
        return {
            'años':  delta.years,
            'meses': delta.months,
            'dias':  delta.days,
            'texto': f'{delta.years} año(s), {delta.months} mes(es), {delta.days} día(s)',
        }

    def clean(self):
        if self.fecha_inicio and self.fecha_fin:
            if self.fecha_fin < self.fecha_inicio:
                raise ValidationError(
                    'La fecha de fin no puede ser anterior a la fecha de inicio.'
                )

    def __str__(self):
        return f'{self.cargo} en {self.institucion}'


class Capacitacion(models.Model):
    """
    EF-12 sección 1.8: cursos, seminarios y talleres.
    """
    TIPO_CHOICES = [
        ('CURSO',     'Curso'),
        ('SEMINARIO', 'Seminario'),
        ('TALLER',    'Taller'),
    ]

    postulante   = models.ForeignKey(
        Postulante, on_delete=models.CASCADE, related_name='capacitaciones'
    )
    tipo_evento  = models.CharField(max_length=10, choices=TIPO_CHOICES)
    nombre       = models.CharField(max_length=200)
    institucion  = models.CharField(max_length=200)
    fecha_inicio = models.DateField()
    fecha_fin    = models.DateField()
    horas        = models.PositiveIntegerField()
    documento    = models.FileField(
        upload_to=upload_capacitacion,
        validators=[validar_pdf]
    )

    class Meta:
        verbose_name        = 'Capacitación'
        verbose_name_plural = 'Capacitaciones'
        ordering            = ['-fecha_inicio']

    def __str__(self):
        return f'{self.nombre} — {self.horas}h'


class Publicacion(models.Model):
    """
    EF-12 sección 1.7: publicaciones e investigaciones académicas.
    """
    TIPO_CHOICES = [
        ('PUBLICACION',   'Publicación'),
        ('INVESTIGACION', 'Trabajo de investigación'),
    ]

    postulante  = models.ForeignKey(
        Postulante, on_delete=models.CASCADE, related_name='publicaciones'
    )
    titulo      = models.CharField(max_length=300)
    tipo        = models.CharField(max_length=15, choices=TIPO_CHOICES)
    medio       = models.CharField(max_length=150)
    fecha       = models.DateField()
    relacionado = models.BooleanField(default=False)
    documento   = models.FileField(
        upload_to=upload_publicacion,
        validators=[validar_pdf]
    )

    class Meta:
        verbose_name        = 'Publicación'
        verbose_name_plural = 'Publicaciones'
        ordering            = ['-fecha']

    def __str__(self):
        return self.titulo


class Inhabilidades(models.Model):
    """
    EF-12 sección 1.9: las 13 preguntas de inhabilidades.
    """
    postulante = models.OneToOneField(
        Postulante, on_delete=models.CASCADE, related_name='inhabilidades'
    )

    p1_goce_derechos         = models.BooleanField(null=True)
    p2_inhabilitado_comercio = models.BooleanField(null=True)
    p3_mora_obligaciones     = models.BooleanField(null=True)
    p4_vinculo_financiero    = models.BooleanField(null=True)
    p5_funcionario_iess      = models.BooleanField(null=True)
    p6_interes_aseguradoras  = models.BooleanField(null=True)
    p7_removido_organismo    = models.BooleanField(null=True)
    p7_institucion           = models.CharField(max_length=100, blank=True)
    p7_cargo                 = models.CharField(max_length=100, blank=True)
    p7_fecha_fin             = models.DateField(null=True, blank=True)
    p7_motivo                = models.CharField(max_length=300, blank=True)
    p8_sri                   = models.BooleanField(null=True)
    p9_castigo_financiero    = models.BooleanField(null=True)
    p10_litigio_iess         = models.BooleanField(null=True)
    p11_procesado_corrupcion = models.BooleanField(null=True)
    p12_contraloria          = models.BooleanField(null=True)
    p13_uafe                 = models.BooleanField(null=True)

    class Meta:
        verbose_name        = 'Inhabilidades'
        verbose_name_plural = 'Inhabilidades'

    def __str__(self):
        return f'Inhabilidades — {self.postulante.codigo_unico}'
