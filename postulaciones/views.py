import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.forms import inlineformset_factory
from django.template.loader import get_template
from django.http import HttpResponse
from xhtml2pdf import pisa
from .models import (
    Postulante, FamiliarIESS, FormacionAcademica,
    ExperienciaProfesional, Capacitacion, Publicacion, Inhabilidades
)


def get_or_create_postulante(user):
    postulante, _ = Postulante.objects.get_or_create(usuario=user)
    return postulante


@login_required
def paso_info_personal(request):
    postulante = get_or_create_postulante(request.user)
    if request.method == 'POST':
        postulante.nombres          = request.POST.get('nombres', '')
        postulante.apellidos        = request.POST.get('apellidos', '')
        postulante.genero           = request.POST.get('genero', '')
        postulante.fecha_nacimiento = request.POST.get('fecha_nacimiento') or None
        postulante.nacionalidad     = request.POST.get('nacionalidad', '')
        postulante.estado_civil     = request.POST.get('estado_civil', '')
        postulante.conyuge_nombres  = request.POST.get('conyuge_nombres', '')
        postulante.conyuge_cedula   = request.POST.get('conyuge_cedula', '')
        postulante.save()
        messages.success(request, 'Información personal guardada.')
        return redirect('paso_domicilio')
    return render(request, 'postulaciones/paso_info_personal.html', {
        'postulante': postulante, 'paso': 1, 'total_pasos': 8
    })


@login_required
def paso_domicilio(request):
    postulante = get_or_create_postulante(request.user)
    if request.method == 'POST':
        postulante.pais               = request.POST.get('pais', '')
        postulante.provincia          = request.POST.get('provincia', '')
        postulante.ciudad             = request.POST.get('ciudad', '')
        postulante.calle_principal    = request.POST.get('calle_principal', '')
        postulante.numero             = request.POST.get('numero', '')
        postulante.calle_secundaria   = request.POST.get('calle_secundaria', '')
        postulante.sector_domicilio   = request.POST.get('sector_domicilio', '')
        postulante.referencia         = request.POST.get('referencia', '')
        postulante.telefono_celular   = request.POST.get('telefono_celular', '')
        postulante.telefono_domicilio = request.POST.get('telefono_domicilio', '')
        postulante.email_secundario   = request.POST.get('email_secundario', '')
        postulante.save()
        messages.success(request, 'Domicilio guardado.')
        return redirect('paso_sector')
    return render(request, 'postulaciones/paso_domicilio.html', {
        'postulante': postulante, 'paso': 2, 'total_pasos': 8
    })


@login_required
def paso_sector(request):
    postulante = get_or_create_postulante(request.user)

    if request.method == 'POST':
        postulante.sector = request.POST.get('sector', '')

        # Manejar correctamente el booleano
        tiene_org = request.POST.get('tiene_organizacion')
        if tiene_org == 'True':
            postulante.tiene_organizacion = True
        elif tiene_org == 'False':
            postulante.tiene_organizacion = False
        else:
            postulante.tiene_organizacion = None

        postulante.nombre_organizacion = request.POST.get('nombre_organizacion', '')

        if 'doc_organizacion' in request.FILES:
            postulante.doc_organizacion = request.FILES['doc_organizacion']

        postulante.save()
        messages.success(request, 'Sector guardado.')
        return redirect('paso_familiares')

    return render(request, 'postulaciones/paso_sector.html', {
        'postulante': postulante,
        'paso': 3, 'total_pasos': 8
    })


@login_required
def paso_familiares(request):
    postulante = get_or_create_postulante(request.user)

    if request.method == 'POST':
        # Detectar todos los familiares enviados por el JS
        ids = set()
        for key in request.POST:
            if key.startswith('familiar_nombres_'):
                ids.add(key.replace('familiar_nombres_', ''))

        for fid in ids:
            nombres     = request.POST.get(f'familiar_nombres_{fid}', '').strip()
            parentesco  = request.POST.get(f'familiar_parentesco_{fid}', '')
            institucion = request.POST.get(f'familiar_institucion_{fid}', '')
            area        = request.POST.get(f'familiar_area_{fid}', '').strip()
            cargo       = request.POST.get(f'familiar_cargo_{fid}', '').strip()

            if nombres and parentesco and institucion and area and cargo:
                FamiliarIESS.objects.create(
                    postulante=postulante,
                    nombres=nombres,
                    parentesco=parentesco,
                    institucion=institucion,
                    area=area,
                    cargo=cargo,
                )

        messages.success(request, 'Familiares guardados.')
        return redirect('paso_formacion')

    familiares = FamiliarIESS.objects.filter(postulante=postulante)
    return render(request, 'postulaciones/paso_familiares.html', {
        'familiares': familiares,
        'postulante': postulante,
        'paso': 4, 'total_pasos': 8
    })


@login_required
def paso_formacion(request):
    postulante = get_or_create_postulante(request.user)

    if request.method == 'POST':
        ids = set()
        for key in request.POST:
            if key.startswith('formacion_nivel_'):
                ids.add(key.replace('formacion_nivel_', ''))

        for fid in ids:
            nivel          = request.POST.get(f'formacion_nivel_{fid}', '')
            tipo           = request.POST.get(f'formacion_tipo_{fid}', '')
            institucion    = request.POST.get(f'formacion_institucion_{fid}', '').strip()
            area           = request.POST.get(f'formacion_area_{fid}', '')
            titulo         = request.POST.get(f'formacion_titulo_{fid}', '').strip()
            num_senescyt   = request.POST.get(f'formacion_senescyt_{fid}', '').strip()
            fecha_senescyt = request.POST.get(f'formacion_fecha_senescyt_{fid}', '')
            documento      = request.FILES.get(f'formacion_documento_{fid}')

            if nivel and institucion and titulo and num_senescyt and fecha_senescyt and documento:
                FormacionAcademica.objects.create(
                    postulante=postulante,
                    nivel=nivel,
                    tipo=tipo,
                    institucion=institucion,
                    area_estudios=area,
                    titulo=titulo,
                    num_senescyt=num_senescyt,
                    fecha_senescyt=fecha_senescyt,
                    documento=documento,
                )

        messages.success(request, 'Formación académica guardada.')
        return redirect('paso_experiencia')

    formaciones = FormacionAcademica.objects.filter(postulante=postulante)
    return render(request, 'postulaciones/paso_formacion.html', {
        'formaciones': formaciones,
        'postulante':  postulante,
        'paso': 5, 'total_pasos': 8
    })


@login_required
def eliminar_formacion(request, pk):
    postulante = get_or_create_postulante(request.user)
    formacion  = get_object_or_404(FormacionAcademica, pk=pk, postulante=postulante)
    formacion.delete()
    messages.success(request, 'Formación eliminada.')
    return redirect('paso_formacion')


@login_required
def paso_experiencia(request):
    postulante = get_or_create_postulante(request.user)

    if request.method == 'POST':
        ids = set()
        for key in request.POST:
            if key.startswith('exp_tipo_'):
                ids.add(key.replace('exp_tipo_', ''))

        for eid in ids:
            tipo         = request.POST.get(f'exp_tipo_{eid}', '')
            area         = request.POST.get(f'exp_area_{eid}', '')
            cargo        = request.POST.get(f'exp_cargo_{eid}', '').strip()
            institucion  = request.POST.get(f'exp_institucion_{eid}', '').strip()
            fecha_inicio = request.POST.get(f'exp_fecha_inicio_{eid}', '')
            fecha_fin    = request.POST.get(f'exp_fecha_fin_{eid}', '')
            descripcion  = request.POST.get(f'exp_descripcion_{eid}', '').strip()
            documento    = request.FILES.get(f'exp_documento_{eid}')

            if tipo and cargo and institucion and fecha_inicio and fecha_fin and descripcion and documento:
                ExperienciaProfesional.objects.create(
                    postulante=postulante,
                    tipo=tipo,
                    actividades_area=area,
                    cargo=cargo,
                    institucion=institucion,
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin,
                    descripcion=descripcion,
                    documento=documento,
                )

        messages.success(request, 'Experiencia profesional guardada.')
        return redirect('paso_capacitacion')

    experiencias = ExperienciaProfesional.objects.filter(postulante=postulante)
    return render(request, 'postulaciones/paso_experiencia.html', {
        'experiencias': experiencias,
        'postulante':   postulante,
        'paso': 6, 'total_pasos': 8
    })


@login_required
def eliminar_experiencia(request, pk):
    postulante   = get_or_create_postulante(request.user)
    experiencia  = get_object_or_404(ExperienciaProfesional, pk=pk, postulante=postulante)
    experiencia.delete()
    messages.success(request, 'Experiencia eliminada.')
    return redirect('paso_experiencia')


@login_required
def paso_capacitacion(request):
    postulante = get_or_create_postulante(request.user)

    if request.method == 'POST':
        # Capacitaciones
        cap_ids = set()
        for key in request.POST:
            if key.startswith('cap_tipo_'):
                cap_ids.add(key.replace('cap_tipo_', ''))

        for cid in cap_ids:
            tipo        = request.POST.get(f'cap_tipo_{cid}', '')
            nombre      = request.POST.get(f'cap_nombre_{cid}', '').strip()
            institucion = request.POST.get(f'cap_institucion_{cid}', '').strip()
            fecha_inicio= request.POST.get(f'cap_fecha_inicio_{cid}', '')
            fecha_fin   = request.POST.get(f'cap_fecha_fin_{cid}', '')
            horas       = request.POST.get(f'cap_horas_{cid}', 0)
            documento   = request.FILES.get(f'cap_documento_{cid}')

            if tipo and nombre and institucion and fecha_inicio and fecha_fin and horas and documento:
                Capacitacion.objects.create(
                    postulante=postulante,
                    tipo_evento=tipo,
                    nombre=nombre,
                    institucion=institucion,
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin,
                    horas=horas,
                    documento=documento,
                )

        # Publicaciones
        pub_ids = set()
        for key in request.POST:
            if key.startswith('pub_titulo_'):
                pub_ids.add(key.replace('pub_titulo_', ''))

        for pid in pub_ids:
            titulo      = request.POST.get(f'pub_titulo_{pid}', '').strip()
            tipo        = request.POST.get(f'pub_tipo_{pid}', '')
            medio       = request.POST.get(f'pub_medio_{pid}', '').strip()
            fecha       = request.POST.get(f'pub_fecha_{pid}', '')
            relacionado = request.POST.get(f'pub_relacionado_{pid}', 'False') == 'True'
            documento   = request.FILES.get(f'pub_documento_{pid}')

            if titulo and tipo and medio and fecha and documento:
                Publicacion.objects.create(
                    postulante=postulante,
                    titulo=titulo,
                    tipo=tipo,
                    medio=medio,
                    fecha=fecha,
                    relacionado=relacionado,
                    documento=documento,
                )

        messages.success(request, 'Capacitación y publicaciones guardadas.')
        return redirect('paso_inhabilidades')

    capacitaciones = Capacitacion.objects.filter(postulante=postulante)
    publicaciones  = Publicacion.objects.filter(postulante=postulante)
    return render(request, 'postulaciones/paso_capacitacion.html', {
        'capacitaciones': capacitaciones,
        'publicaciones':  publicaciones,
        'postulante':     postulante,
        'paso': 7, 'total_pasos': 8
    })


@login_required
def eliminar_capacitacion(request, pk):
    postulante   = get_or_create_postulante(request.user)
    capacitacion = get_object_or_404(Capacitacion, pk=pk, postulante=postulante)
    capacitacion.delete()
    messages.success(request, 'Capacitación eliminada.')
    return redirect('paso_capacitacion')


@login_required
def eliminar_publicacion(request, pk):
    postulante  = get_or_create_postulante(request.user)
    publicacion = get_object_or_404(Publicacion, pk=pk, postulante=postulante)
    publicacion.delete()
    messages.success(request, 'Publicación eliminada.')
    return redirect('paso_capacitacion')


@login_required
def paso_inhabilidades(request):
    postulante     = get_or_create_postulante(request.user)
    inhabilidad, _ = Inhabilidades.objects.get_or_create(postulante=postulante)

    preguntas = [
        ('p1_goce_derechos',         '¿Es ecuatoriano/a y está en pleno goce de los derechos de participación política?'),
        ('p2_inhabilitado_comercio',  '¿Se encuentra inhabilitado para ejercer el comercio?'),
        ('p3_mora_obligaciones',      '¿Está en mora, directa o indirectamente, en el pago de sus obligaciones con el Estado o SuperBancos?'),
        ('p4_vinculo_financiero',     '¿Mantiene algún vínculo con instituciones del sistema financiero o de seguros privados?'),
        ('p5_funcionario_iess',       '¿Es funcionario o empleado del IESS o BIESS?'),
        ('p6_interes_aseguradoras',   '¿Mantiene interés propio o representa a terceros en compañías aseguradoras del sistema de seguridad social?'),
        ('p7_removido_organismo',     '¿En los últimos 5 años, ha sido removido por algún Organismo de Control?'),
        ('p8_sri',                    '¿Mantiene obligaciones pendientes con el SRI?'),
        ('p9_castigo_financiero',     '¿Ha incurrido en los últimos 5 años en castigo de obligaciones por institución financiera?'),
        ('p10_litigio_iess',          '¿Actualmente se encuentra litigando en contra del IESS o BIESS?'),
        ('p11_procesado_corrupcion',  '¿Se encuentra procesado, enjuiciado o condenado por algún delito de corrupción o crimen organizado?'),
        ('p12_contraloria',           '¿Mantiene en firme algún tipo de responsabilidades por la Contraloría General del Estado?'),
        ('p13_uafe',                  '¿Se encuentra registrado en la base de datos de la UAFE?'),
    ]

    if request.method == 'POST':
        for campo, _ in preguntas:
            valor = request.POST.get(campo)
            if valor is not None:
                setattr(inhabilidad, campo, valor == 'True')
        inhabilidad.p7_institucion = request.POST.get('p7_institucion', '')
        inhabilidad.p7_cargo       = request.POST.get('p7_cargo', '')
        inhabilidad.p7_motivo      = request.POST.get('p7_motivo', '')
        fecha_p7 = request.POST.get('p7_fecha_fin')
        inhabilidad.p7_fecha_fin   = fecha_p7 if fecha_p7 else None
        inhabilidad.save()
        messages.success(request, 'Inhabilidades guardadas.')
        return redirect('resumen_postulacion')

    # Construir dict para restaurar radios en el template
    import json
    valores_actuales = {}
    for campo, _ in preguntas:
        val = getattr(inhabilidad, campo, None)
        if val is True:
            valores_actuales[campo] = 'True'
        elif val is False:
            valores_actuales[campo] = 'False'
        else:
            valores_actuales[campo] = ''

    return render(request, 'postulaciones/paso_inhabilidades.html', {
        'inhabilidad':          inhabilidad,
        'postulante':           postulante,
        'preguntas':            preguntas,
        'valores_actuales_json': json.dumps(valores_actuales),
        'paso': 8, 'total_pasos': 8
    })


@login_required
def resumen_postulacion(request):
    postulante = get_object_or_404(Postulante, usuario=request.user)
    if request.method == 'POST':
        postulante.estado = 'ENVIADO'
        postulante.save()
        messages.success(
            request,
            f'Postulación {postulante.codigo_unico} enviada correctamente.'
        )
        return redirect('confirmacion_postulacion')
    return render(request, 'postulaciones/resumen.html', {
        'postulante':     postulante,
        'formaciones':    postulante.formaciones.all(),
        'experiencias':   postulante.experiencias.all(),
        'capacitaciones': postulante.capacitaciones.all(),
        'publicaciones':  postulante.publicaciones.all(),
        'familiares':     postulante.familiares.all(),
        'inhabilidades':  getattr(postulante, 'inhabilidades', None),
    })

@login_required
def eliminar_familiar(request, pk):
    postulante = get_or_create_postulante(request.user)
    familiar   = get_object_or_404(FamiliarIESS, pk=pk, postulante=postulante)
    familiar.delete()
    messages.success(request, 'Familiar eliminado.')
    return redirect('paso_familiares')

@login_required
def confirmacion_postulacion(request):
    postulante = get_object_or_404(Postulante, usuario=request.user)
    return render(request, 'postulaciones/confirmacion.html', {
        'postulante': postulante
    })

@login_required
def paso_inhabilidades(request):
    postulante   = get_or_create_postulante(request.user)
    inhabilidad, _ = Inhabilidades.objects.get_or_create(postulante=postulante)

    preguntas = [
        ('p1_goce_derechos',         '¿Es ecuatoriano/a y está en pleno goce de los derechos de participación política?'),
        ('p2_inhabilitado_comercio',  '¿Se encuentra inhabilitado para ejercer el comercio?'),
        ('p3_mora_obligaciones',      '¿Está en mora, directa o indirectamente, en el pago de sus obligaciones con el Estado o SuperBancos?'),
        ('p4_vinculo_financiero',     '¿Mantiene algún vínculo con instituciones del sistema financiero o de seguros privados?'),
        ('p5_funcionario_iess',       '¿Es funcionario o empleado del IESS o BIESS?'),
        ('p6_interes_aseguradoras',   '¿Mantiene interés propio o representa a terceros en compañías aseguradoras del sistema de seguridad social?'),
        ('p7_removido_organismo',     '¿En los últimos 5 años, ha sido removido por algún Organismo de Control?'),
        ('p8_sri',                    '¿Mantiene obligaciones pendientes con el SRI?'),
        ('p9_castigo_financiero',     '¿Ha incurrido en los últimos 5 años en castigo de obligaciones por institución financiera?'),
        ('p10_litigio_iess',          '¿Actualmente se encuentra litigando en contra del IESS o BIESS?'),
        ('p11_procesado_corrupcion',  '¿Se encuentra procesado, enjuiciado o condenado por algún delito de corrupción o crimen organizado?'),
        ('p12_contraloria',           '¿Mantiene en firme algún tipo de responsabilidades por la Contraloría General del Estado?'),
        ('p13_uafe',                  '¿Se encuentra registrado en la base de datos de la UAFE?'),
    ]

    if request.method == 'POST':
        for campo, _ in preguntas:
            valor = request.POST.get(campo)
            if valor is not None:
                setattr(inhabilidad, campo, valor == 'True')
        inhabilidad.p7_institucion = request.POST.get('p7_institucion', '')
        inhabilidad.p7_cargo       = request.POST.get('p7_cargo', '')
        inhabilidad.p7_motivo      = request.POST.get('p7_motivo', '')
        fecha_p7 = request.POST.get('p7_fecha_fin')
        inhabilidad.p7_fecha_fin   = fecha_p7 if fecha_p7 else None
        inhabilidad.save()
        messages.success(request, 'Inhabilidades guardadas.')
        return redirect('resumen_postulacion')

    return render(request, 'postulaciones/paso_inhabilidades.html', {
        'inhabilidad': inhabilidad,
        'postulante':  postulante,
        'preguntas':   preguntas,
        'paso': 8, 'total_pasos': 8
    })

@login_required
def descargar_pdf(request):
    postulante    = get_object_or_404(Postulante, usuario=request.user)
    familiares    = postulante.familiares.all()
    formaciones   = postulante.formaciones.all()
    experiencias  = postulante.experiencias.all()
    capacitaciones= postulante.capacitaciones.all()
    publicaciones = postulante.publicaciones.all()
    inhabilidades = getattr(postulante, 'inhabilidades', None)

    def si_no(val):
        if val is True:
            return 'Si'
        elif val is False:
            return 'No'
        return '-'

    inh_rows = ''
    if inhabilidades:
        preguntas_inh = [
            ('p1_goce_derechos',         '9.1. Es ecuatoriano/a en pleno goce de derechos de participacion politica?'),
            ('p2_inhabilitado_comercio',  '9.2. Se encuentra inhabilitado para ejercer el comercio?'),
            ('p3_mora_obligaciones',      '9.3. Esta en mora con el Estado o SuperBancos?'),
            ('p4_vinculo_financiero',     '9.4. Mantiene vinculo con instituciones del sistema financiero?'),
            ('p5_funcionario_iess',       '9.5. Es funcionario o empleado del IESS o BIESS?'),
            ('p6_interes_aseguradoras',   '9.6. Mantiene interes en companias aseguradoras?'),
            ('p7_removido_organismo',     '9.7. En los ultimos 5 anos fue removido por algun Organismo de Control?'),
            ('p8_sri',                    '9.8. Mantiene obligaciones pendientes con el SRI?'),
            ('p9_castigo_financiero',     '9.9. Ha incurrido en castigo de obligaciones por institucion financiera?'),
            ('p10_litigio_iess',          '9.10. Se encuentra litigando en contra del IESS/BIESS?'),
            ('p11_procesado_corrupcion',  '9.11. Se encuentra procesado por delito de corrupcion o crimen organizado?'),
            ('p12_contraloria',           '9.12. Mantiene responsabilidades en firme por la Contraloria?'),
            ('p13_uafe',                  '9.13. Se encuentra registrado en la base de datos de la UAFE?'),
        ]
        for campo, etiqueta in preguntas_inh:
            val = getattr(inhabilidades, campo, None)
            inh_rows += f'<tr><td>{etiqueta}</td><td class="r">{si_no(val)}</td></tr>'

    # Familiares
    fam_rows = ''
    for f in familiares:
        fam_rows += f'<tr><td>{f.nombres}</td><td>{f.get_parentesco_display()}</td><td>{f.get_institucion_display()}</td><td>{f.area}</td><td>{f.cargo}</td></tr>'

    # Formaciones
    form_rows = ''
    for f in formaciones:
        form_rows += f'<tr><td>{f.get_nivel_display()}</td><td>{f.get_tipo_display()}</td><td>{f.titulo}</td><td>{f.institucion}</td><td>{f.get_area_estudios_display()}</td><td>{f.num_senescyt}</td><td>{f.fecha_senescyt.strftime("%d/%m/%Y")}</td></tr>'

    # Experiencias
    exp_rows = ''
    for e in experiencias:
        tiempo = e.tiempo_calculado
        exp_rows += f'<tr><td>{e.get_tipo_display()}</td><td>{e.cargo}</td><td>{e.institucion}</td><td>{e.get_actividades_area_display()}</td><td>{e.fecha_inicio.strftime("%d/%m/%Y")}</td><td>{e.fecha_fin.strftime("%d/%m/%Y")}</td><td>{tiempo["texto"]}</td></tr>'

    # Capacitaciones
    cap_rows = ''
    for c in capacitaciones:
        cap_rows += f'<tr><td>{c.get_tipo_evento_display()}</td><td>{c.nombre}</td><td>{c.institucion}</td><td>{c.fecha_inicio.strftime("%d/%m/%Y")}</td><td>{c.fecha_fin.strftime("%d/%m/%Y")}</td><td>{c.horas}h</td></tr>'

    # Publicaciones
    pub_rows = ''
    for p in publicaciones:
        pub_rows += f'<tr><td>{p.titulo}</td><td>{p.get_tipo_display()}</td><td>{p.medio}</td><td>{p.fecha.strftime("%d/%m/%Y")}</td></tr>'

    html = f'''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: Helvetica, Arial, sans-serif; font-size: 10px; color: #222; }}
.header {{ background-color: #003580; color: white; padding: 12px 20px; margin-bottom: 16px; }}
.header h1 {{ font-size: 14px; margin-bottom: 2px; }}
.header p {{ font-size: 9px; }}
.codigo {{ font-size: 12px; font-weight: bold; color: #003580; margin-bottom: 14px; padding: 6px 10px; border: 2px solid #003580; display: inline-block; }}
h2 {{ font-size: 11px; color: #003580; border-bottom: 1px solid #003580; padding-bottom: 3px; margin: 14px 0 8px 0; text-transform: uppercase; }}
.grid {{ width: 100%; margin-bottom: 8px; }}
.grid td {{ padding: 3px 6px; font-size: 9px; vertical-align: top; width: 33%; }}
.lbl {{ color: #666; font-size: 8px; display: block; margin-bottom: 1px; }}
.val {{ font-weight: bold; }}
table.t {{ width: 100%; border-collapse: collapse; margin-bottom: 10px; font-size: 9px; }}
table.t th {{ background-color: #003580; color: white; padding: 4px 6px; text-align: left; font-size: 8px; }}
table.t td {{ padding: 3px 6px; border-bottom: 1px solid #ddd; }}
.inh {{ width: 100%; border-collapse: collapse; font-size: 9px; }}
.inh td {{ padding: 3px 6px; border-bottom: 1px solid #eee; }}
.inh .r {{ font-weight: bold; width: 25px; text-align: center; }}
.decl {{ background-color: #f8f8f8; border: 1px solid #ddd; padding: 10px 12px; margin: 12px 0; font-size: 8px; line-height: 1.6; }}
.decl p {{ margin-bottom: 4px; }}
.nd {{ color: #999; font-style: italic; font-size: 9px; margin-bottom: 8px; }}
</style>
</head>
<body>
<div class="header">
<h1>INSTITUTO ECUATORIANO DE SEGURIDAD SOCIAL</h1>
<p>Concurso Publico de Meritos y Oposicion - Directorio BIESS</p>
</div>
<div class="codigo">Codigo: {postulante.codigo_unico} | Fecha: {postulante.creado_en.strftime("%d/%m/%Y")}</div>

<h2>1. Sector de Postulacion</h2>
<table class="grid">
<tr>
<td colspan="2"><span class="lbl">Cargo al que postula</span><span class="val">{postulante.get_sector_display()}</span></td>
<td><span class="lbl">Organizacion</span><span class="val">{postulante.nombre_organizacion or "No"}</span></td>
</tr>
</table>

<h2>2. Informacion Personal</h2>
<table class="grid">
<tr>
<td><span class="lbl">Nombres</span><span class="val">{postulante.nombres}</span></td>
<td><span class="lbl">Apellidos</span><span class="val">{postulante.apellidos}</span></td>
<td><span class="lbl">Cedula</span><span class="val">{postulante.usuario.cedula}
</span></td>
</tr>
<tr>
<td><span class="lbl">Genero</span><span class="val">{postulante.get_genero_display()}</span></td>
<td><span class="lbl">Fecha nacimiento</span><span class="val">{postulante.fecha_nacimiento.strftime("%d/%m/%Y") if postulante.fecha_nacimiento else "-"}</span></td>
<td><span class="lbl">Nacionalidad</span><span class="val">{postulante.nacionalidad}</span></td>
</tr>
<tr>
<td><span class="lbl">Estado civil</span><span class="val">{postulante.get_estado_civil_display()}</span></td>
<td><span class="lbl">Conyuge</span><span class="val">{postulante.conyuge_nombres or "No aplica"}</span></td>
<td><span class="lbl">Cedula conyuge</span><span class="val">{postulante.conyuge_cedula or "No aplica"}</span></td>
</tr>
</table>

<h2>3. Domicilio y Contacto</h2>
<table class="grid">
<tr>
<td><span class="lbl">Pais</span><span class="val">{postulante.pais}</span></td>
<td><span class="lbl">Provincia</span><span class="val">{postulante.provincia}</span></td>
<td><span class="lbl">Ciudad</span><span class="val">{postulante.ciudad}</span></td>
</tr>
<tr>
<td><span class="lbl">Calle principal</span><span class="val">{postulante.calle_principal} {postulante.numero}</span></td>
<td><span class="lbl">Calle secundaria</span><span class="val">{postulante.calle_secundaria}</span></td>
<td><span class="lbl">Sector</span><span class="val">{postulante.sector_domicilio}</span></td>
</tr>
<tr>
<td><span class="lbl">Celular</span><span class="val">{postulante.telefono_celular}</span></td>
<td><span class="lbl">Telefono domicilio</span><span class="val">{postulante.telefono_domicilio or "No registra"}</span></td>
<td><span class="lbl">Correo</span><span class="val">{postulante.usuario.email}</span></td>
</tr>
</table>

<h2>4. Familiares en IESS/BIESS</h2>
{"<table class='t'><thead><tr><th>Nombres</th><th>Parentesco</th><th>Institucion</th><th>Area</th><th>Cargo</th></tr></thead><tbody>" + fam_rows + "</tbody></table>" if fam_rows else "<p class='nd'>No registra familiares.</p>"}

<h2>5. Formacion Academica</h2>
{"<table class='t'><thead><tr><th>Nivel</th><th>Tipo</th><th>Titulo</th><th>Institucion</th><th>Area</th><th>SENESCYT</th><th>Fecha</th></tr></thead><tbody>" + form_rows + "</tbody></table>" if form_rows else "<p class='nd'>No registra formacion academica.</p>"}

<h2>6. Experiencia Profesional</h2>
{"<table class='t'><thead><tr><th>Tipo</th><th>Cargo</th><th>Institucion</th><th>Area</th><th>Inicio</th><th>Fin</th><th>Tiempo</th></tr></thead><tbody>" + exp_rows + "</tbody></table>" if exp_rows else "<p class='nd'>No registra experiencia profesional.</p>"}

<h2>7. Capacitacion</h2>
{"<table class='t'><thead><tr><th>Tipo</th><th>Nombre</th><th>Institucion</th><th>Inicio</th><th>Fin</th><th>Horas</th></tr></thead><tbody>" + cap_rows + "</tbody></table>" if cap_rows else "<p class='nd'>No registra capacitaciones.</p>"}

<h2>8. Publicaciones</h2>
{"<table class='t'><thead><tr><th>Titulo</th><th>Tipo</th><th>Medio</th><th>Fecha</th></tr></thead><tbody>" + pub_rows + "</tbody></table>" if pub_rows else "<p class='nd'>No registra publicaciones.</p>"}

<h2>9. Inhabilidades</h2>
{"<table class='inh'>" + inh_rows + "</table>" if inh_rows else "<p class='nd'>No registra inhabilidades.</p>"}

<div class="decl">
<p><strong>Declaracion del postulante:</strong></p>
<p>1. Autorizo de manera libre y voluntaria, emitiendo consentimiento explicito al Instituto Ecuatoriano de Seguridad Social, para el uso de mis datos
personales dentro del concurso de méritos y oposición para la selección de los Miembros Principales y Alternos del Directorio del Banco del Instituto
Ecuatoriano de Seguridad Social (BIESS), en Representación de los Afiliados, Jubilados y Empleadores, de conformidad con lo prescrito en el articulo
7 de la Ley Orgánica de Protección de Datos Personales.</p>
<p>2. Declaro que la información del presente formulario y documentación adjunta corresponde a la verdad y autorizo al Instituto Ecuatoriano de
Seguridad Social para que se compruebe ante cualquier organismo público o privado su veracidad.
</p>
<p>3. Acepto expresamente cumplir con las normas aplicables al concurso de méritos y oposición para la selección de los Miembros Principales y Alternos
del Directorio del Banco del Instituto Ecuatoriano de Seguridad Social (BIESS), en Representación de los Afiliados, Jubilados y Empleadores; así como
las resoluciones y disposiciones impartidas por el Instituto Ecuatoriano de Seguridad Social. En caso de incumplimiento de requisitos o encontrarme
inmerso/a en las prohibiciones o inhabilidades acepto mi descalificación del proceso.
</p>
<p>4. Acepto que mi nombre como postulante al concurso de méritos y oposición para la selección de los Miembros Principales y Alternos del Directorio del
Banco del Instituto Ecuatoriano de Seguridad Social (BIESS), en Representación de los Afiliados, Jubilados y Empleadores; sea publicado en la página
web del IESS - BIESS.</p>
<p>5. El presente formulario, debe ser impreso y con firma manuscrita, entregado junto con los requisitos solicitados, en el lugar, fecha y horario
establecido por el Instituto Ecuatoriano de Seguridad Social.
</p>
</div>

<table width="100%" style="margin-top:20px;">
<tr>
<td width="40%"></td>
<td width="20%" align="center">
<br/><br/><br/><br/><br/>
<div style="border-top:1px solid #333; padding-top:6px; font-size:9px;">
{postulante.nombres} {postulante.apellidos}<br/>
C.I.: {postulante.cedula}<br/>
Firma del Postulante
</div>
</td>
<td width="40%"></td>
</tr>
</table>
</body>
</html>'''

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="postulacion_{postulante.codigo_unico}.pdf"'
    pisa.CreatePDF(html, dest=response)
    return response

def solo_staff(view_func):
    """Decorator: solo usuarios staff pueden acceder"""
    from functools import wraps
    from django.shortcuts import redirect
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


@solo_staff
def admin_postulaciones(request):
    # Filtros
    sector = request.GET.get('sector', '')
    estado = request.GET.get('estado', '')
    buscar = request.GET.get('buscar', '')

    postulantes = Postulante.objects.select_related('usuario').all().order_by('-creado_en')

    if sector:
        postulantes = postulantes.filter(sector=sector)
    if estado:
        postulantes = postulantes.filter(estado=estado)
    if buscar:
        postulantes = postulantes.filter(
            cedula__icontains=buscar
        ) | postulantes.filter(
            nombres__icontains=buscar
        ) | postulantes.filter(
            apellidos__icontains=buscar
        )

    # Contadores para dashboard
    total           = Postulante.objects.count()
    por_sector      = Postulante.objects.values('sector').annotate(total=Count('id'))
    por_estado      = Postulante.objects.values('estado').annotate(total=Count('id'))
    total_afiliados = Postulante.objects.filter(sector='AFILIADO').count()
    total_jubilados = Postulante.objects.filter(sector='JUBILADO').count()
    total_empleadores = Postulante.objects.filter(sector='EMPLEADOR').count()
    total_enviados  = Postulante.objects.filter(estado='ENVIADO').count()
    total_borradores= Postulante.objects.filter(estado='BORRADOR').count()

    return render(request, 'postulaciones/admin_postulaciones.html', {
        'postulantes':       postulantes,
        'total':             total,
        'total_afiliados':   total_afiliados,
        'total_jubilados':   total_jubilados,
        'total_empleadores': total_empleadores,
        'total_enviados':    total_enviados,
        'total_borradores':  total_borradores,
        'sector_actual':     sector,
        'estado_actual':     estado,
        'buscar':            buscar,
        'SECTOR_CHOICES':    Postulante.SECTOR_CHOICES,
        'ESTADO_CHOICES':    Postulante.ESTADO_CHOICES,
    })


@solo_staff
def admin_detalle_postulante(request, pk):
    postulante = get_object_or_404(Postulante, pk=pk)
    return render(request, 'postulaciones/admin_detalle.html', {
        'postulante':     postulante,
        'familiares':     postulante.familiares.all(),
        'formaciones':    postulante.formaciones.all(),
        'experiencias':   postulante.experiencias.all(),
        'capacitaciones': postulante.capacitaciones.all(),
        'publicaciones':  postulante.publicaciones.all(),
        'inhabilidades':  getattr(postulante, 'inhabilidades', None),
    })


@solo_staff
def admin_cambiar_estado(request, pk):
    if request.method == 'POST':
        postulante = get_object_or_404(Postulante, pk=pk)
        nuevo_estado = request.POST.get('estado')
        if nuevo_estado:
            postulante.estado = nuevo_estado
            postulante.save()
            messages.success(request, f'Estado actualizado a {postulante.get_estado_display()}.')
    return redirect('admin_postulaciones')


@solo_staff
def exportar_excel(request):
    postulantes = Postulante.objects.select_related('usuario').all().order_by('-creado_en')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Postulaciones'

    # Estilos
    header_font    = Font(bold=True, color='FFFFFF', size=10)
    header_fill    = PatternFill(start_color='003580', end_color='003580', fill_type='solid')
    header_align   = Alignment(horizontal='center', vertical='center', wrap_text=True)
    center_align   = Alignment(horizontal='center', vertical='center')

    # Cabeceras
    headers = [
        'N°', 'Código', 'Cédula', 'Apellidos', 'Nombres',
        'Sector', 'Estado', 'Correo', 'Celular',
        'País', 'Provincia', 'Ciudad',
        'Formaciones', 'Experiencias', 'Capacitaciones',
        'Fecha registro'
    ]

    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font    = header_font
        cell.fill    = header_fill
        cell.alignment = header_align

    ws.row_dimensions[1].height = 30

    # Datos
    for idx, p in enumerate(postulantes, 1):
        fila = [
            idx,
            p.codigo_unico,
            p.cedula,
            p.apellidos,
            p.nombres,
            p.get_sector_display(),
            p.get_estado_display(),
            p.usuario.email,
            p.telefono_celular,
            p.pais,
            p.provincia,
            p.ciudad,
            p.formaciones.count(),
            p.experiencias.count(),
            p.capacitaciones.count(),
            p.creado_en.strftime('%d/%m/%Y %H:%M'),
        ]
        for col, valor in enumerate(fila, 1):
            cell = ws.cell(row=idx + 1, column=col, value=valor)
            cell.alignment = center_align

    # Ancho de columnas
    anchos = [5, 15, 12, 20, 20, 25, 15, 30, 13, 12, 15, 15, 12, 12, 12, 18]
    for col, ancho in enumerate(anchos, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = ancho

    # Segunda hoja — resumen por sector
    ws2 = wb.create_sheet('Resumen')
    ws2.append(['Sector', 'Total'])
    for row in Postulante.objects.values('sector').annotate(total=Count('id')):
        sector_display = dict(Postulante.SECTOR_CHOICES).get(row['sector'], row['sector'])
        ws2.append([sector_display, row['total']])

    ws2.append([])
    ws2.append(['Estado', 'Total'])
    for row in Postulante.objects.values('estado').annotate(total=Count('id')):
        estado_display = dict(Postulante.ESTADO_CHOICES).get(row['estado'], row['estado'])
        ws2.append([estado_display, row['total']])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="postulaciones_biess.xlsx"'
    wb.save(response)
    return response

@solo_staff
def admin_pdf_postulante(request, pk):
    postulante     = get_object_or_404(Postulante, pk=pk)
    familiares     = postulante.familiares.all()
    formaciones    = postulante.formaciones.all()
    experiencias   = postulante.experiencias.all()
    capacitaciones = postulante.capacitaciones.all()
    publicaciones  = postulante.publicaciones.all()
    inhabilidades  = getattr(postulante, 'inhabilidades', None)

    def si_no(val):
        if val is True: return 'Si'
        elif val is False: return 'No'
        return '-'

    inh_rows = ''
    if inhabilidades:
        preguntas_inh = [
            ('p1_goce_derechos',        '1. Es ecuatoriano/a en pleno goce de derechos de participacion politica?'),
            ('p2_inhabilitado_comercio', '2. Se encuentra inhabilitado para ejercer el comercio?'),
            ('p3_mora_obligaciones',     '3. Esta en mora con el Estado o SuperBancos?'),
            ('p4_vinculo_financiero',    '4. Mantiene vinculo con instituciones del sistema financiero?'),
            ('p5_funcionario_iess',      '5. Es funcionario o empleado del IESS o BIESS?'),
            ('p6_interes_aseguradoras',  '6. Mantiene interes en companias aseguradoras?'),
            ('p7_removido_organismo',    '7. En los ultimos 5 anos fue removido por algun Organismo de Control?'),
            ('p8_sri',                   '8. Mantiene obligaciones pendientes con el SRI?'),
            ('p9_castigo_financiero',    '9. Ha incurrido en castigo de obligaciones por institucion financiera?'),
            ('p10_litigio_iess',         '10. Se encuentra litigando en contra del IESS/BIESS?'),
            ('p11_procesado_corrupcion', '11. Se encuentra procesado por delito de corrupcion o crimen organizado?'),
            ('p12_contraloria',          '12. Mantiene responsabilidades en firme por la Contraloria?'),
            ('p13_uafe',                 '13. Se encuentra registrado en la base de datos de la UAFE?'),
        ]
        for campo, etiqueta in preguntas_inh:
            val = getattr(inhabilidades, campo, None)
            inh_rows += f'<tr><td>{etiqueta}</td><td class="r">{si_no(val)}</td></tr>'

    fam_rows  = ''.join(f'<tr><td>{f.nombres}</td><td>{f.get_parentesco_display()}</td><td>{f.get_institucion_display()}</td><td>{f.area}</td><td>{f.cargo}</td></tr>' for f in familiares)
    form_rows = ''.join(f'<tr><td>{f.get_nivel_display()}</td><td>{f.get_tipo_display()}</td><td>{f.titulo}</td><td>{f.institucion}</td><td>{f.get_area_estudios_display()}</td><td>{f.num_senescyt}</td><td>{f.fecha_senescyt.strftime("%d/%m/%Y")}</td></tr>' for f in formaciones)
    exp_rows  = ''.join(f'<tr><td>{e.get_tipo_display()}</td><td>{e.cargo}</td><td>{e.institucion}</td><td>{e.get_actividades_area_display()}</td><td>{e.fecha_inicio.strftime("%d/%m/%Y")}</td><td>{e.fecha_fin.strftime("%d/%m/%Y")}</td><td>{e.tiempo_calculado["texto"]}</td></tr>' for e in experiencias)
    cap_rows  = ''.join(f'<tr><td>{c.get_tipo_evento_display()}</td><td>{c.nombre}</td><td>{c.institucion}</td><td>{c.fecha_inicio.strftime("%d/%m/%Y")}</td><td>{c.fecha_fin.strftime("%d/%m/%Y")}</td><td>{c.horas}h</td></tr>' for c in capacitaciones)
    pub_rows  = ''.join(f'<tr><td>{p.titulo}</td><td>{p.get_tipo_display()}</td><td>{p.medio}</td><td>{p.fecha.strftime("%d/%m/%Y")}</td></tr>' for p in publicaciones)

    html = f'''<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:Helvetica,Arial,sans-serif; font-size:10px; color:#222; }}
.header {{ background-color:#003580; color:white; padding:12px 20px; margin-bottom:16px; }}
.header h1 {{ font-size:14px; margin-bottom:2px; }}
.header p {{ font-size:9px; }}
.codigo {{ font-size:12px; font-weight:bold; color:#003580; margin-bottom:14px; padding:6px 10px; border:2px solid #003580; display:inline-block; }}
h2 {{ font-size:11px; color:#003580; border-bottom:1px solid #003580; padding-bottom:3px; margin:14px 0 8px 0; text-transform:uppercase; }}
.grid {{ width:100%; margin-bottom:8px; }}
.grid td {{ padding:3px 6px; font-size:9px; vertical-align:top; width:33%; }}
.lbl {{ color:#666; font-size:8px; display:block; margin-bottom:1px; }}
.val {{ font-weight:bold; }}
table.t {{ width:100%; border-collapse:collapse; margin-bottom:10px; font-size:9px; }}
table.t th {{ background-color:#003580; color:white; padding:4px 6px; text-align:left; font-size:8px; }}
table.t td {{ padding:3px 6px; border-bottom:1px solid #ddd; }}
.inh {{ width:100%; border-collapse:collapse; font-size:9px; }}
.inh td {{ padding:3px 6px; border-bottom:1px solid #eee; }}
.inh .r {{ font-weight:bold; width:25px; text-align:center; }}
.decl {{ background-color:#f8f8f8; border:1px solid #ddd; padding:10px 12px; margin:12px 0; font-size:8px; line-height:1.6; }}
.decl p {{ margin-bottom:4px; }}
.nd {{ color:#999; font-style:italic; font-size:9px; margin-bottom:8px; }}
</style></head><body>
<div class="header">
<h1>INSTITUTO ECUATORIANO DE SEGURIDAD SOCIAL</h1>
<p>Concurso Publico de Meritos y Oposicion - Directorio BIESS</p>
</div>
<div class="codigo">Codigo: {postulante.codigo_unico} | Fecha: {postulante.creado_en.strftime("%d/%m/%Y")}</div>
<h2>1. Informacion Personal</h2>
<table class="grid"><tr>
<td><span class="lbl">Nombres</span><span class="val">{postulante.nombres}</span></td>
<td><span class="lbl">Apellidos</span><span class="val">{postulante.apellidos}</span></td>
<td><span class="lbl">Cedula</span><span class="val">{postulante.usuario.cedula}</span></td>
</tr><tr>
<td><span class="lbl">Genero</span><span class="val">{postulante.get_genero_display()}</span></td>
<td><span class="lbl">Fecha nacimiento</span><span class="val">{postulante.fecha_nacimiento.strftime("%d/%m/%Y") if postulante.fecha_nacimiento else "-"}</span></td>
<td><span class="lbl">Nacionalidad</span><span class="val">{postulante.nacionalidad}</span></td>
</tr><tr>
<td><span class="lbl">Estado civil</span><span class="val">{postulante.get_estado_civil_display()}</span></td>
<td><span class="lbl">Conyuge</span><span class="val">{postulante.conyuge_nombres or "No aplica"}</span></td>
<td><span class="lbl">Cedula conyuge</span><span class="val">{postulante.conyuge_cedula or "No aplica"}</span></td>
</tr></table>
<h2>2. Domicilio y Contacto</h2>
<table class="grid"><tr>
<td><span class="lbl">Pais</span><span class="val">{postulante.pais}</span></td>
<td><span class="lbl">Provincia</span><span class="val">{postulante.provincia}</span></td>
<td><span class="lbl">Ciudad</span><span class="val">{postulante.ciudad}</span></td>
</tr><tr>
<td><span class="lbl">Calle principal</span><span class="val">{postulante.calle_principal} {postulante.numero}</span></td>
<td><span class="lbl">Calle secundaria</span><span class="val">{postulante.calle_secundaria}</span></td>
<td><span class="lbl">Sector</span><span class="val">{postulante.sector_domicilio}</span></td>
</tr><tr>
<td><span class="lbl">Celular</span><span class="val">{postulante.telefono_celular}</span></td>
<td><span class="lbl">Telefono domicilio</span><span class="val">{postulante.telefono_domicilio or "No registra"}</span></td>
<td><span class="lbl">Correo</span><span class="val">{postulante.usuario.email}</span></td>
</tr></table>
<h2>3. Sector de Postulacion</h2>
<table class="grid"><tr>
<td colspan="2"><span class="lbl">Cargo al que postula</span><span class="val">{postulante.get_sector_display()}</span></td>
<td><span class="lbl">Organizacion</span><span class="val">{postulante.nombre_organizacion or "No"}</span></td>
</tr></table>
<h2>4. Familiares en IESS/BIESS</h2>
{"<table class='t'><thead><tr><th>Nombres</th><th>Parentesco</th><th>Institucion</th><th>Area</th><th>Cargo</th></tr></thead><tbody>" + fam_rows + "</tbody></table>" if fam_rows else "<p class='nd'>No registra familiares.</p>"}
<h2>5. Formacion Academica</h2>
{"<table class='t'><thead><tr><th>Nivel</th><th>Tipo</th><th>Titulo</th><th>Institucion</th><th>Area</th><th>SENESCYT</th><th>Fecha</th></tr></thead><tbody>" + form_rows + "</tbody></table>" if form_rows else "<p class='nd'>No registra formacion academica.</p>"}
<h2>6. Experiencia Profesional</h2>
{"<table class='t'><thead><tr><th>Tipo</th><th>Cargo</th><th>Institucion</th><th>Area</th><th>Inicio</th><th>Fin</th><th>Tiempo</th></tr></thead><tbody>" + exp_rows + "</tbody></table>" if exp_rows else "<p class='nd'>No registra experiencia profesional.</p>"}
<h2>7. Capacitacion</h2>
{"<table class='t'><thead><tr><th>Tipo</th><th>Nombre</th><th>Institucion</th><th>Inicio</th><th>Fin</th><th>Horas</th></tr></thead><tbody>" + cap_rows + "</tbody></table>" if cap_rows else "<p class='nd'>No registra capacitaciones.</p>"}
<h2>8. Publicaciones</h2>
{"<table class='t'><thead><tr><th>Titulo</th><th>Tipo</th><th>Medio</th><th>Fecha</th></tr></thead><tbody>" + pub_rows + "</tbody></table>" if pub_rows else "<p class='nd'>No registra publicaciones.</p>"}
<h2>9. Inhabilidades</h2>
{"<table class='inh'>" + inh_rows + "</table>" if inh_rows else "<p class='nd'>No registra inhabilidades.</p>"}
<div class="decl">
<p><strong>Declaracion del postulante:</strong></p>
<p>1. Autorizo de manera libre y voluntaria al IESS el uso de mis datos personales dentro del concurso de meritos y oposicion.</p>
<p>2. Declaro que la informacion del presente formulario corresponde a la verdad.</p>
<p>3. Acepto cumplir con las normas aplicables al concurso.</p>
<p>4. Acepto que mi nombre sea publicado en la pagina web del IESS/BIESS.</p>
</div>
<table width="100%" style="margin-top:20px;">
<tr><td width="40%"></td>
<td width="20%" align="center"><br/><br/><br/><br/><br/>
<div style="border-top:1px solid #333; padding-top:6px; font-size:9px;">
{postulante.nombres} {postulante.apellidos}<br/>C.I.: {postulante.cedula}<br/>Firma del Postulante
</div></td>
<td width="40%"></td></tr>
</table>
</body></html>'''

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="postulacion_{postulante.codigo_unico}.pdf"'
    pisa.CreatePDF(html, dest=response)
    return response