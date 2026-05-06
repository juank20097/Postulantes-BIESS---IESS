import requests
import random
import logging
from django.utils import timezone
from datetime import timedelta
from decouple import config

logger = logging.getLogger(__name__)

CORREO_ENDPOINT = config('WS_CORREO')

# ── Estilos base del correo ───────────────────────────────────────────────────
ESTILO_BASE = """
<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;border:1px solid #e0e0e0;border-radius:8px;overflow:hidden;">
  <div style="background-color:#003580;padding:20px 24px;">
    <h2 style="color:white;margin:0;font-size:18px;">INSTITUTO ECUATORIANO DE SEGURIDAD SOCIAL</h2>
    <p style="color:#cce0ff;margin:4px 0 0;font-size:13px;">Concurso Público de Méritos y Oposición — Directorio BIESS</p>
  </div>
  <div style="padding:24px;">
    {contenido}
  </div>
  <div style="background-color:#f5f5f5;padding:12px 24px;font-size:11px;color:#888;text-align:center;">
    Este es un mensaje automático. Por favor no responda a este correo.
  </div>
</div>
"""

# ── Mensajes por estado ───────────────────────────────────────────────────────
NOTIFICACIONES = {
    'ENVIADO': {
        'asunto': 'Postulación recibida — BIESS Concurso Directorio',
        'titulo': 'Postulación Recibida',
        'cuerpo': lambda p: f"""
            <p>Estimado/a <strong>{p.nombres} {p.apellidos}</strong>,</p>
            <p>Nos complace informarle que su postulación ha sido <strong style="color:#003580;">recibida correctamente</strong>.</p>
            <table style="width:100%;border-collapse:collapse;margin:16px 0;">
              <tr><td style="padding:6px 12px;background:#f0f4ff;font-weight:bold;width:40%;">Código de postulación</td>
                  <td style="padding:6px 12px;font-size:18px;font-weight:bold;color:#003580;">{p.codigo_unico}</td></tr>
              <tr><td style="padding:6px 12px;background:#f0f4ff;font-weight:bold;">Sector</td>
                  <td style="padding:6px 12px;">{p.get_sector_display()}</td></tr>
              <tr><td style="padding:6px 12px;background:#f0f4ff;font-weight:bold;">Estado</td>
                  <td style="padding:6px 12px;color:#198754;font-weight:bold;">Enviada</td></tr>
            </table>
            <p>Su postulación está siendo revisada por el equipo de Talento Humano. Le notificaremos sobre cualquier cambio en el proceso.</p>
        """,
    },
    'EN_REVISION': {
        'asunto': 'Su postulación está en revisión — BIESS',
        'titulo': 'Postulación en Revisión',
        'cuerpo': lambda p: f"""
            <p>Estimado/a <strong>{p.nombres} {p.apellidos}</strong>,</p>
            <p>Le informamos que su postulación con código <strong style="color:#003580;">{p.codigo_unico}</strong> se encuentra actualmente <strong>en proceso de revisión</strong> por parte de la Subdirección Nacional de Gestión de Talento Humano.</p>
            <p>Una vez concluida la revisión, recibirá una notificación con el resultado.</p>
        """,
    },
    'HABILITADO': {
        'asunto': '✅ Su postulación ha sido habilitada — BIESS',
        'titulo': 'Postulación Habilitada',
        'cuerpo': lambda p: f"""
            <p>Estimado/a <strong>{p.nombres} {p.apellidos}</strong>,</p>
            <p>Con mucho agrado le comunicamos que su postulación con código <strong style="color:#003580;">{p.codigo_unico}</strong> ha sido <strong style="color:#198754;">HABILITADA</strong> para continuar en el proceso del Concurso Público de Méritos y Oposición para la Designación de Miembros del Directorio del BIESS.</p>
            <p>Próximamente recibirá información sobre las siguientes etapas del proceso.</p>
        """,
    },
    'INHABILITADO': {
        'asunto': '❌ Resultado de su postulación — BIESS',
        'titulo': 'Postulación No Habilitada',
        'cuerpo': lambda p: f"""
            <p>Estimado/a <strong>{p.nombres} {p.apellidos}</strong>,</p>
            <p>Lamentamos informarle que su postulación con código <strong style="color:#003580;">{p.codigo_unico}</strong> ha sido declarada <strong style="color:#dc3545;">NO HABILITADA</strong> para continuar en el proceso, por cuanto se encuentra dentro de las prohibiciones e inhabilidades establecidas en el art. 13 de la Resolución No. C.D. 701.</p>
            <p>Si considera que existe un error, puede comunicarse con la Subdirección Nacional de Gestión de Talento Humano del IESS.</p>
        """,
    },
    'FASE_MERITOS': {
        'asunto': '🏆 Ha pasado a la Fase de Méritos — BIESS',
        'titulo': 'Fase de Méritos',
        'cuerpo': lambda p: f"""
            <p>Estimado/a <strong>{p.nombres} {p.apellidos}</strong>,</p>
            <p>Nos complace informarle que su postulación con código <strong style="color:#003580;">{p.codigo_unico}</strong> ha avanzado a la <strong style="color:#0d6efd;">FASE DE MÉRITOS</strong> del Concurso Público.</p>
            <p>En esta etapa se evaluarán sus títulos académicos, experiencia profesional, capacitaciones y publicaciones. Le notificaremos el puntaje obtenido una vez concluida la calificación.</p>
        """,
    },
    'EVAL_TECNICA': {
        'asunto': '📋 Convocatoria a Evaluación Técnica — BIESS',
        'titulo': 'Evaluación Técnica',
        'cuerpo': lambda p: f"""
            <p>Estimado/a <strong>{p.nombres} {p.apellidos}</strong>,</p>
            <p>Le informamos que su postulación con código <strong style="color:#003580;">{p.codigo_unico}</strong> ha avanzado a la etapa de <strong style="color:#0d6efd;">EVALUACIÓN TÉCNICA</strong> del Concurso Público.</p>
            <p>Recibirá información adicional sobre la fecha, hora y lugar de la evaluación a través de los canales oficiales del IESS.</p>
        """,
    },
    'FINALIZADO': {
        'asunto': 'Proceso concluido — BIESS Concurso Directorio',
        'titulo': 'Proceso Finalizado',
        'cuerpo': lambda p: f"""
            <p>Estimado/a <strong>{p.nombres} {p.apellidos}</strong>,</p>
            <p>Le comunicamos que el proceso de evaluación correspondiente a su postulación con código <strong style="color:#003580;">{p.codigo_unico}</strong> ha <strong>FINALIZADO</strong>.</p>
            <p>Los resultados finales serán publicados en la página web institucional del IESS y del BIESS. Agradecemos su participación en este proceso.</p>
        """,
    },
}


# ── Función base de envío ─────────────────────────────────────────────────────

def _enviar_correo(email, asunto, titulo, html_contenido):
    """Envía un correo usando el WS externo."""
    cuerpo = {
        "para":          [email],
        "cc":            [],
        "cco":           [],
        "asunto":        asunto,
        "titulo":        titulo,
        "mensajeHtml":   ESTILO_BASE.format(contenido=html_contenido),
        "adjuntoBase64": "",
        "nombreArchivo": ""
    }
    try:
        response = requests.post(CORREO_ENDPOINT, json=cuerpo, timeout=10)
        return response.status_code == 200
    except Exception as e:
        logger.error(f'Error enviando correo a {email}: {e}')
        return False


# ── OTP ───────────────────────────────────────────────────────────────────────

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
    """Envía el OTP de verificación de cuenta."""
    html = f"""
        <p>Estimado/a postulante,</p>
        <p>Su código de verificación para acceder al formulario de postulación es:</p>
        <div style="text-align:center;margin:24px 0;">
          <span style="font-size:36px;font-weight:bold;letter-spacing:12px;color:#003580;
                       background:#f0f4ff;padding:12px 24px;border-radius:8px;">{codigo}</span>
        </div>
        <p>Este código es válido por <strong>5 minutos</strong>.</p>
        <p style="color:#888;font-size:12px;">Si no realizó este registro, ignore este mensaje.</p>
    """
    return _enviar_correo(
        email=email,
        asunto='Código de verificación — BIESS Postulaciones',
        titulo='Verificación de cuenta',
        html_contenido=html
    )


# ── Notificación por cambio de estado ────────────────────────────────────────

def notificar_cambio_estado(postulante):
    """
    Envía un correo al postulante cuando su estado cambia.
    Llama desde views.py después de guardar el nuevo estado.
    """
    estado = postulante.estado
    notif  = NOTIFICACIONES.get(estado)

    if not notif:
        logger.info(f'Sin notificación configurada para estado: {estado}')
        return False

    email = postulante.usuario.email
    if not email:
        logger.warning(f'Postulante {postulante.codigo_unico} sin email, no se envía notificación.')
        return False

    ok = _enviar_correo(
        email=email,
        asunto=notif['asunto'],
        titulo=notif['titulo'],
        html_contenido=notif['cuerpo'](postulante)
    )

    if ok:
        logger.info(f'Notificación [{estado}] enviada a {email} ({postulante.codigo_unico})')
    else:
        logger.error(f'Fallo notificación [{estado}] a {email} ({postulante.codigo_unico})')

    return ok
