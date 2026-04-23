from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
import uuid


class PostulanteUserManager(BaseUserManager):
    def create_user(self, cedula, email, password=None):
        if not cedula:
            raise ValueError('La cédula es obligatoria')
        if not email:
            raise ValueError('El email es obligatorio')
        user = self.model(
            cedula=cedula,
            email=self.normalize_email(email),
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, cedula, email, password=None):
        user = self.create_user(cedula, email, password)
        user.is_staff     = True
        user.is_superuser = True
        user.is_active    = True
        user.save(using=self._db)
        return user


class PostulanteUser(AbstractBaseUser, PermissionsMixin):
    """
    Usuario del sistema.
    EF-11: autenticación con cédula + contraseña.
    is_active=False hasta que active su cuenta por email.
    """
    cedula     = models.CharField(max_length=10, unique=True)
    email      = models.EmailField(unique=True)
    nombre_completo = models.CharField(max_length=200, blank=True)
    is_active  = models.BooleanField(default=False)
    is_staff   = models.BooleanField(default=False)
    fecha_reg  = models.DateTimeField(auto_now_add=True)

    # Esto soluciona el conflicto con auth.User
    groups = models.ManyToManyField(
        'auth.Group',
        blank=True,
        related_name='postulante_users',  # <-- este es el fix
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        blank=True,
        related_name='postulante_users',  # <-- este es el fix
        verbose_name='user permissions',
    )

    USERNAME_FIELD  = 'cedula'
    REQUIRED_FIELDS = ['email']
    objects = PostulanteUserManager()

    class Meta:
        verbose_name        = 'Usuario postulante'
        verbose_name_plural = 'Usuarios postulantes'

    def __str__(self):
        return f'{self.cedula} — {self.email}'


class RegistroCI(models.Model):
    """
    EF-11 paso 4: controla los intentos fallidos de validación
    con el Registro Civil (DIGERCIC).
    Máximo 3 intentos, bloqueo de 10 minutos.
    """
    cedula          = models.CharField(max_length=10, unique=True)
    intentos        = models.PositiveSmallIntegerField(default=0)
    bloqueado_hasta = models.DateTimeField(null=True, blank=True)
    creado_en       = models.DateTimeField(auto_now_add=True)
    actualizado_en  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Registro CI'
        verbose_name_plural = 'Registros CI'

    def esta_bloqueado(self):
        from django.utils import timezone
        if self.bloqueado_hasta and timezone.now() < self.bloqueado_hasta:
            return True
        return False

    def incrementar_intento(self):
        from django.utils import timezone
        from datetime import timedelta
        self.intentos += 1
        if self.intentos >= 3:
            self.bloqueado_hasta = timezone.now() + timedelta(minutes=10)
        self.save()

    def resetear(self):
        self.intentos        = 0
        self.bloqueado_hasta = None
        self.save()

    def __str__(self):
        return f'CI {self.cedula} — intentos: {self.intentos}'


class TokenActivacion(models.Model):
    """
    EF-11 paso 4: token de activación de cuenta
    enviado al correo del postulante al registrarse.
    """
    usuario   = models.OneToOneField(
        PostulanteUser, on_delete=models.CASCADE, related_name='token_activacion'
    )
    token     = models.UUIDField(default=uuid.uuid4, unique=True)
    expira    = models.DateTimeField()
    usado     = models.BooleanField(default=False)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Token de activación'

    def __str__(self):
        return f'Activación {self.usuario.cedula} — usado: {self.usado}'


class RecuperacionPassword(models.Model):
    """
    EF-11 paso 6: token de recuperación de contraseña.
    Se valida cédula + fecha expedición o código dactilar
    con DIGERCIC antes de enviar el correo.
    """
    usuario   = models.ForeignKey(
        PostulanteUser, on_delete=models.CASCADE, related_name='recuperaciones'
    )
    token     = models.UUIDField(default=uuid.uuid4, unique=True)
    expira    = models.DateTimeField()
    usado     = models.BooleanField(default=False)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Recuperación de contraseña'
        verbose_name_plural = 'Recuperaciones de contraseña'

    def __str__(self):
        return f'Recuperación {self.usuario.cedula} — usado: {self.usado}'
