import requests
import logging

logger = logging.getLogger(__name__)

WS_URL = 'https://ws.iess.gob.ec/iess-ws-registro-civil/webresources/registro/civil/obtenerDatosPersona'

def consultar_registro_civil(cedula):
    """
    Consulta el WS del IESS para obtener datos personales por cédula.
    Retorna dict con los datos o None si falla.
    """
    try:
        response = requests.post(
            WS_URL,
            json={'numeroDocumento': cedula},
            timeout=10,
            verify=False  # algunos WS internos tienen certificados autofirmados
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
    """
    Convierte la respuesta del WS al formato de los modelos Django.
    """
    if not cuerpo:
        return None

    nombre_completo = cuerpo.get('nombre', '')
    partes = nombre_completo.strip().split()

    # El formato es: APELLIDO1 APELLIDO2 NOMBRE1 NOMBRE2
    if len(partes) >= 4:
        apellidos = f'{partes[0]} {partes[1]}'
        nombres   = ' '.join(partes[2:])
    elif len(partes) == 3:
        apellidos = partes[0]
        nombres   = f'{partes[1]} {partes[2]}'
    else:
        apellidos = nombre_completo
        nombres   = ''

    # Mapear género
    genero_rc = cuerpo.get('genero', '').upper()
    genero = 'M' if genero_rc == 'MASCULINO' else 'F'

    # Mapear estado civil
    estado_civil_rc = cuerpo.get('estadoCivil', '').upper()
    estados_civil_map = {
        'SOLTERO':     'SOLTERO',
        'SOLTERA':     'SOLTERO',
        'CASADO':      'CASADO',
        'CASADA':      'CASADO',
        'DIVORCIADO':  'DIVORCIADO',
        'DIVORCIADA':  'DIVORCIADO',
        'VIUDO':       'VIUDO',
        'VIUDA':       'VIUDO',
        'UNION LIBRE': 'UNION_HECHO',
        'UNION DE HECHO': 'UNION_HECHO',
    }
    estado_civil = estados_civil_map.get(estado_civil_rc, 'SOLTERO')

    # Formatear fecha nacimiento de DD/MM/YYYY a YYYY-MM-DD
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