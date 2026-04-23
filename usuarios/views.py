from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .forms import RegistroForm, LoginForm
from postulaciones.services import consultar_registro_civil, parsear_datos_rc
import json


def registro(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_postulaciones')
        return redirect('paso_info_personal')

    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Precargar datos RC en el postulante
            cedula = form.cleaned_data['cedula']
            cuerpo = consultar_registro_civil(cedula)
            if cuerpo:
                datos = parsear_datos_rc(cuerpo)
                if datos:
                    from postulaciones.models import Postulante
                    postulante, _ = Postulante.objects.get_or_create(usuario=user)
                    postulante.cedula           = cedula
                    postulante.nombres          = datos['nombres']
                    postulante.apellidos        = datos['apellidos']
                    postulante.genero           = datos['genero']
                    postulante.estado_civil     = datos['estado_civil']
                    postulante.fecha_nacimiento = datos['fecha_nacimiento']
                    postulante.nacionalidad     = datos['nacionalidad']
                    postulante.save()

            login(request, user)
            messages.success(request, 'Cuenta creada correctamente. Bienvenido/a.')
            return redirect('paso_info_personal')

        return render(request, 'usuarios/registro.html', {'form': form})

    return render(request, 'usuarios/registro.html', {})


def consultar_cedula_ajax(request):
    if request.method == 'POST':
        try:
            body   = json.loads(request.body)
            cedula = body.get('cedula', '').strip()
        except Exception:
            return JsonResponse({'ok': False, 'error': 'Petición inválida.'})

        if not cedula or len(cedula) != 10 or not cedula.isdigit():
            return JsonResponse({'ok': False, 'error': 'Cédula inválida.'})

        # Verificar si ya existe cuenta
        from usuarios.models import PostulanteUser
        if PostulanteUser.objects.filter(cedula=cedula).exists():
            return JsonResponse({'ok': False, 'error': 'Ya existe una cuenta registrada con esta cédula.'})

        cuerpo = consultar_registro_civil(cedula)
        if not cuerpo:
            return JsonResponse({'ok': False, 'error': 'No se encontró información para esta cédula en el Registro Civil.'})

        datos = parsear_datos_rc(cuerpo)
        if not datos:
            return JsonResponse({'ok': False, 'error': 'Error al procesar los datos del Registro Civil.'})

        return JsonResponse({
            'ok': True,
            'datos': {
                'nombres':          datos['nombres'],
                'apellidos':        datos['apellidos'],
                'genero':           datos['genero'],
                'genero_texto':     'Masculino' if datos['genero'] == 'M' else 'Femenino',
                'estado_civil':     datos['estado_civil'],
                'fecha_nacimiento': str(datos['fecha_nacimiento']) if datos['fecha_nacimiento'] else '',
                'nacionalidad':     datos['nacionalidad'],
            }
        })

    return JsonResponse({'ok': False, 'error': 'Método no permitido.'})


def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_postulaciones')
        return redirect('paso_info_personal')

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        cedula   = form.cleaned_data['cedula']
        password = form.cleaned_data['password']
        user     = authenticate(request, username=cedula, password=password)
        if user is not None:
            login(request, user)
            if user.is_staff:
                return redirect('admin_postulaciones')
            return redirect('paso_info_personal')
        else:
            messages.error(request, 'Cédula o contraseña incorrectos.')

    return render(request, 'usuarios/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'Ha cerrado sesión correctamente.')
    return redirect('login')