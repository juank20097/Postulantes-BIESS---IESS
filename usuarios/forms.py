from django import forms
from django.contrib.auth.password_validation import validate_password
from .models import PostulanteUser


class RegistroForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su contraseña'
        })
    )
    password2 = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Repita su contraseña'
        })
    )

    class Meta:
        model  = PostulanteUser
        fields = ['cedula', 'email']
        widgets = {
            'cedula': forms.TextInput(attrs={
                'class':       'form-control',
                'maxlength':   '10',
                'placeholder': 'Ingrese su número de cédula',
            }),
            'email': forms.EmailInput(attrs={
                'class':       'form-control',
                'placeholder': 'correo@ejemplo.com',
            }),
        }

    def clean_cedula(self):
        cedula = self.cleaned_data.get('cedula')
        if not cedula.isdigit():
            raise forms.ValidationError('La cédula solo debe contener números.')
        if len(cedula) != 10:
            raise forms.ValidationError('La cédula debe tener exactamente 10 dígitos.')
        if PostulanteUser.objects.filter(cedula=cedula).exists():
            raise forms.ValidationError('Ya existe una cuenta registrada con esta cédula.')
        return cedula

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if PostulanteUser.objects.filter(email=email).exists():
            raise forms.ValidationError('Ya existe una cuenta registrada con este correo.')
        return email

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        validate_password(password1)
        return password1

    def clean(self):
        cleaned   = super().clean()
        password1 = cleaned.get('password1')
        password2 = cleaned.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Las contraseñas no coinciden.')
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.is_active = True
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    cedula = forms.CharField(
        label='Número de cédula',
        max_length=10,
        widget=forms.TextInput(attrs={
            'class':       'form-control',
            'placeholder': 'Ingrese su cédula',
            'autofocus':   True,
        })
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class':       'form-control',
            'placeholder': 'Ingrese su contraseña',
        })
    )