from django.db import models
from django.core.exceptions import ValidationError
import uuid


def validar_pdf(archivo):
    if not archivo.name.lower().endswith('.pdf'):
        raise ValidationError('Solo se permiten archivos PDF.')


class Postulante(models.Model):
    """
    Modelo central del formulario BIESS.
    EF-12: agrupa toda la información del postulante
    separada en secciones según el RF.
    """

    # ── Choices ───────────────────────────────────────────────────────────────
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

    # ── Relación con usuario ──────────────────────────────────────────────────
    usuario      = models.OneToOneField(
        'usuarios.PostulanteUser',
        on_delete=models.CASCADE,
        related_name='postulante'
    )
    codigo_unico = models.CharField(max_length=20, unique=True, blank=True)
    sector       = models.CharField(max_length=15, choices=SECTOR_CHOICES, blank=True)
    estado       = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='BORRADOR')

    # ── Sección 1.1: Información personal ────────────────────────────────────
    # Campos readonly: vienen de DIGERCIC vía interoperabilidad
    nombres          = models.CharField(max_length=100, blank=True)
    apellidos        = models.CharField(max_length=100, blank=True)
    cedula           = models.CharField(max_length=10, blank=True)
    genero           = models.CharField(max_length=1, choices=GENERO_CHOICES, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    # EF-12 1.1.6: si nacionalidad != ecuatoriana el sistema cierra la postulación
    nacionalidad     = models.CharField(max_length=60, blank=True)
    estado_civil     = models.CharField(max_length=15, choices=ESTADO_CIVIL_CHOICES, blank=True)
    # EF-12 1.1.7.1: condicional si casado/unión de hecho
    conyuge_nombres  = models.CharField(max_length=100, blank=True)
    conyuge_cedula   = models.CharField(max_length=10, blank=True)

    # ── Sección 1.2: Información domiciliaria y de contacto ───────────────────
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
    # email_1 viene del usuario (PostulanteUser.email)
    email_secundario   = models.EmailField(blank=True)

    # ── Sección 1.3: Información adicional — familiar en IESS/BIESS ──────────
    # Ver modelo FamiliarIESS (FK → Postulante)

    # ── Sección 1.4: Sector de postulación y organización de respaldo ─────────
    # EF-12 1.4.1.3 / 1.4.2.3 / 1.4.3.3
    tiene_organizacion  = models.BooleanField(null=True, blank=True)
    nombre_organizacion = models.CharField(max_length=200, blank=True)
    doc_organizacion    = models.FileField(
        upload_to='organizaciones/',
        null=True, blank=True,
        validators=[validar_pdf]
    )  # EF-12: máx. 4 MB

    # ── Timestamps ────────────────────────────────────────────────────────────
    creado_en  = models.DateTimeField(auto_now_add=True)
    modificado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Postulante'
        verbose_name_plural = 'Postulantes'

    def save(self, *args, **kwargs):
        # EF-12: el formulario contará con un código de numeración único
        if not self.codigo_unico:
            self.codigo_unico = f'BIESS-{str(uuid.uuid4())[:8].upper()}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.codigo_unico} — {self.apellidos} {self.nombres}'


class FamiliarIESS(models.Model):
    """
    EF-12 sección 1.3: familiares dentro del segundo grado
    de consanguinidad y cuarto de afinidad trabajando en IESS/BIESS.
    Permite múltiples registros por postulante (botón Agregar).
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
    Solo niveles tercer nivel en adelante (requisito del concurso).
    Documento PDF máx. 2 MB.
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
        upload_to='formacion/',
        validators=[validar_pdf]
    )  # máx. 2 MB — validar en form

    class Meta:
        verbose_name        = 'Formación académica'
        verbose_name_plural = 'Formaciones académicas'
        ordering            = ['-fecha_senescyt']

    def __str__(self):
        return f'{self.titulo} — {self.postulante.codigo_unico}'


class ExperienciaProfesional(models.Model):
    """
    EF-12 sección 1.6: experiencia profesional.
    El sistema calcula automáticamente años/meses/días
    a partir de las fechas ingresadas.
    Documento PDF máx. 2 MB por experiencia.
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
    # EF-12 1.6.7: máximo 1000 caracteres
    descripcion      = models.TextField(max_length=1000)
    documento        = models.FileField(
        upload_to='experiencia/',
        validators=[validar_pdf]
    )  # máx. 2 MB

    class Meta:
        verbose_name        = 'Experiencia profesional'
        verbose_name_plural = 'Experiencias profesionales'
        ordering            = ['-fecha_inicio']

    @property
    def tiempo_calculado(self):
        """
        EF-12 1.6: el sistema calcula automáticamente la experiencia
        visualizando el tiempo en años, meses y días.
        """
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
    Documento PDF máx. 2 MB por evento.
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
        upload_to='capacitacion/',
        validators=[validar_pdf]
    )  # máx. 2 MB

    class Meta:
        verbose_name        = 'Capacitación'
        verbose_name_plural = 'Capacitaciones'
        ordering            = ['-fecha_inicio']

    def __str__(self):
        return f'{self.nombre} — {self.horas}h'


class Publicacion(models.Model):
    """
    EF-12 sección 1.7: publicaciones e investigaciones académicas.
    Condicional: solo si el postulante indica que cuenta con ellas.
    Documento PDF máx. 2 MB por publicación.
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
    # EF-12 1.7.1.5: ¿guarda relación con el campo de ejercicio o formación?
    relacionado = models.BooleanField(default=False)
    documento   = models.FileField(
        upload_to='publicaciones/',
        validators=[validar_pdf]
    )  # máx. 2 MB

    class Meta:
        verbose_name        = 'Publicación'
        verbose_name_plural = 'Publicaciones'
        ordering            = ['-fecha']

    def __str__(self):
        return self.titulo


class Inhabilidades(models.Model):
    """
    EF-12 sección 1.9: las 13 preguntas de inhabilidades.
    Todas obligatorias. OneToOne con Postulante.
    p7 tiene campos adicionales condicionales si la respuesta es True.
    """
    postulante = models.OneToOneField(
        Postulante, on_delete=models.CASCADE, related_name='inhabilidades'
    )

    # 1.9.1 — ¿Es ecuatoriano/a y está en pleno goce de derechos?
    p1_goce_derechos         = models.BooleanField(null=True)
    # 1.9.2 — ¿Se encuentra inhabilitado para ejercer el comercio?
    p2_inhabilitado_comercio = models.BooleanField(null=True)
    # 1.9.3 — ¿Está en mora con el Estado o SuperBancos?
    p3_mora_obligaciones     = models.BooleanField(null=True)
    # 1.9.4 — ¿Mantiene vínculo con instituciones del sistema financiero?
    p4_vinculo_financiero    = models.BooleanField(null=True)
    # 1.9.5 — ¿Es funcionario o empleado del IESS/BIESS?
    p5_funcionario_iess      = models.BooleanField(null=True)
    # 1.9.6 — ¿Mantiene interés en compañías aseguradoras del sistema?
    p6_interes_aseguradoras  = models.BooleanField(null=True)
    # 1.9.7 — ¿En los últimos 5 años fue removido por un Organismo de Control?
    p7_removido_organismo    = models.BooleanField(null=True)
    # Condicionales EF-12 1.7.1.7.1.x — solo si p7 = True
    p7_institucion           = models.CharField(max_length=100, blank=True)
    p7_cargo                 = models.CharField(max_length=100, blank=True)
    p7_fecha_fin             = models.DateField(null=True, blank=True)
    p7_motivo                = models.CharField(max_length=300, blank=True)
    # 1.9.8 — ¿Mantiene obligaciones pendientes con el SRI?
    p8_sri                   = models.BooleanField(null=True)
    # 1.9.9 — ¿Ha incurrido en castigo de obligaciones por institución financiera?
    p9_castigo_financiero    = models.BooleanField(null=True)
    # 1.9.10 — ¿Actualmente litiga en contra del IESS/BIESS?
    p10_litigio_iess         = models.BooleanField(null=True)
    # 1.9.11 — ¿Procesado por delito de corrupción o crimen organizado?
    p11_procesado_corrupcion = models.BooleanField(null=True)
    # 1.9.12 — ¿Mantiene responsabilidades en firme por la Contraloría?
    p12_contraloria          = models.BooleanField(null=True)
    # 1.9.13 — ¿Registrado en la base de datos de la UAFE?
    p13_uafe                 = models.BooleanField(null=True)

    class Meta:
        verbose_name        = 'Inhabilidades'
        verbose_name_plural = 'Inhabilidades'

    def __str__(self):
        return f'Inhabilidades — {self.postulante.codigo_unico}'