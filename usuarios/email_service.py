import requests
import random
import logging
from django.utils import timezone
from datetime import timedelta
from decouple import config

logger = logging.getLogger(__name__)

CORREO_ENDPOINT = config('WS_CORREO')


def generar_otp():
    return str(random.randint(100000, 999999))


def crear_otp(usuario):
    """Genera y guarda un OTP nuevo para el usuario, reemplazando el anterior."""
    from .models import OTPRegistro
    codigo = generar_otp()
    expira = timezone.now() + timedelta(minutes=5)
    OTPRegistro.objects.update_or_create(
        usuario=usuario,
        defaults={'codigo': codigo, 'expira': expira, 'verificado': False}
    )
    return codigo


def enviar_otp_correo(email, codigo):
    """Llama al servicio externo de correo con el OTP generado."""
    cuerpo = {
        "para": [email],
        "cc": [],
        "cco": [],
        "asunto": "Código de verificación — BIESS Postulaciones",
        "titulo": "Verificación de cuenta",
        "mensajeHtml": f"""
            <p>Estimado/a postulante,</p>
            <p>Su código de verificación para acceder al formulario de postulación es:</p>
            <h2 style="letter-spacing:8px; color:#003580;">{codigo}</h2>
            <p>Este código es válido por <strong>5 minutos</strong>.</p>
            <p>Si no realizó este registro, ignore este mensaje.</p>
        """,
        "adjuntoBase64": "",
        "nombreArchivo": ""
    }
    try:
        response = requests.post(CORREO_ENDPOINT, json=cuerpo, timeout=10)
        return response.status_code == 200
    except Exception as e:
        logger.error(f'Error enviando OTP a {email}: {e}')
        return False