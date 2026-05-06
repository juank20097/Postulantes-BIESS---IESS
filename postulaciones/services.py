import requests
import logging
from decouple import config

logger = logging.getLogger(__name__)

WS_URL            = config('WS_REGISTRO_CIVIL')
WS_CALIFICACION   = config('WS_CALIFICACION_DERECHO')
CEDULAS_EMPLEADOR = [c.strip() for c in config('CEDULA_EMPLEADOR', default='').split(',') if c.strip()]


def consultar_registro_civil(cedula):
    try:
        response = requests.post(
            WS_URL,
            json={'numeroDocumento': cedula},
            timeout=10,
            verify=False
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('codigo') == '1':
                return data.get('cuerpo')
        return None
    except requests.exceptions.Timeout:
        logger.error(f'Timeout consultando RC para cédula {cedula}')
        return None
    except Exception as e:
        logger.error(f'Error consultando RC: {e}')
        return None


def parsear_datos_rc(cuerpo):
    if not cuerpo:
        return None

    nombre_completo = cuerpo.get('nombre', '')
    partes = nombre_completo.strip().split()

    if len(partes) >= 4:
        apellidos = f'{partes[0]} {partes[1]}'
        nombres   = ' '.join(partes[2:])
    elif len(partes) == 3:
        apellidos = partes[0]
        nombres   = f'{partes[1]} {partes[2]}'
    else:
        apellidos = nombre_completo
        nombres   = ''

    genero_rc = cuerpo.get('genero', '').upper()
    genero = 'M' if genero_rc == 'MASCULINO' else 'F'

    estado_civil_rc = cuerpo.get('estadoCivil', '').upper()
    estados_civil_map = {
        'SOLTERO':        'SOLTERO',
        'SOLTERA':        'SOLTERO',
        'CASADO':         'CASADO',
        'CASADA':         'CASADO',
        'DIVORCIADO':     'DIVORCIADO',
        'DIVORCIADA':     'DIVORCIADO',
        'VIUDO':          'VIUDO',
        'VIUDA':          'VIUDO',
        'UNION LIBRE':    'UNION_HECHO',
        'UNION DE HECHO': 'UNION_HECHO',
    }
    estado_civil = estados_civil_map.get(estado_civil_rc, 'SOLTERO')

    fecha_nac_rc = cuerpo.get('fechaNacimiento', '')
    fecha_nacimiento = None
    if fecha_nac_rc:
        try:
            from datetime import datetime
            fecha_nacimiento = datetime.strptime(fecha_nac_rc, '%d/%m/%Y').date()
        except ValueError:
            pass

    return {
        'nombres':          nombres,
        'apellidos':        apellidos,
        'genero':           genero,
        'estado_civil':     estado_civil,
        'fecha_nacimiento': fecha_nacimiento,
        'nacionalidad':     'ECUADOR',
    }


def consultar_calificacion_derecho(cedula):
    """
    Determina todos los sectores disponibles del postulante.
    - Si la cédula está en CEDULAS_EMPLEADOR → agrega EMPLEADOR.
    - Consulta el WS de calificación derecho → agrega AFILIADO o JUBILADO si tiene cobertura.
    - Si termina sin sectores → no puede postular.

    Retorna:
    {
        'puede_postular': bool,
        'sectores': ['AFILIADO', 'EMPLEADOR'],   ← lista completa
        'sector':   'AFILIADO',                   ← pre-asignado si es solo uno, '' si hay varios
        'mensaje':  ''
    }
    """
    sectores = []

    # 1. Verificar si es empleador registrado en .env
    if cedula in CEDULAS_EMPLEADOR:
        logger.info(f'Cédula {cedula} identificada como EMPLEADOR por configuración.')
        sectores.append('EMPLEADOR')

    # 2. Consultar WS de calificación derecho
    from datetime import date
    try:
        response = requests.post(
            WS_CALIFICACION,
            json={
                'cedula':       cedula,
                'fecha':        date.today().strftime('%Y-%m-%d'),
                'contingencia': 14
            },
            timeout=10,
            verify=False
        )
        if response.status_code == 200:
            data            = response.json()
            cobertura       = data.get('cobertura', '')
            tipo_afiliacion = data.get('tipoAfiliacion', '')

            if 'CON COBERTURA' in cobertura.upper():
                if 'jubilado' in tipo_afiliacion.lower():
                    sectores.append('JUBILADO')
                else:
                    sectores.append('AFILIADO')

    except requests.exceptions.Timeout:
        logger.error(f'Timeout consultando calificación derecho para cédula {cedula}')
    except Exception as e:
        logger.error(f'Error consultando calificación derecho: {e}')

    # 3. Evaluar resultado
    if not sectores:
        return {
            'puede_postular': False,
            'sectores':       [],
            'sector':         None,
            'mensaje': (
                'Su postulación NO puede continuar, por cuanto no mantiene '
                'ninguna condición de Afiliado, Jubilado o Empleador ante el IESS '
                '(art. 19 Resolución No. C.D. 701).'
            )
        }

    return {
        'puede_postular': True,
        'sectores':       sectores,
        # Pre-asignado si tiene un solo sector, vacío si tiene varios (elige en paso 3)
        'sector':         sectores[0] if len(sectores) == 1 else '',
        'mensaje':        ''
    }
