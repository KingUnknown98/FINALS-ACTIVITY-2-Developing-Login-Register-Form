from django import forms
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .models import Profile


class RegistrationForm(UserCreationForm):
    contact = forms.CharField(max_length=254, label='Email or mobile number')

    class Meta(UserCreationForm.Meta):
        fields = ('username', 'contact')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password2'].widget.attrs['placeholder'] = (
            'Use at least 8 characters with letters and numbers.'
        )

    def clean_password1(self):
        password = self.cleaned_data.get('password1', '')
        if password and (
            not any(character.isalpha() for character in password)
            or not any(character.isdigit() for character in password)
        ):
            raise forms.ValidationError('Password must include both letters and numbers.')
        return password

    def clean_contact(self):
        contact = self.cleaned_data['contact'].strip()
        if '@' in contact:
            try:
                EmailValidator()(contact)
            except ValidationError:
                raise forms.ValidationError('Enter a valid email address or mobile number.')
        else:
            digits = ''.join(character for character in contact if character.isdigit())
            if len(digits) < 7 or any(character not in '+-() .0123456789' for character in contact):
                raise forms.ValidationError('Enter a valid email address or mobile number.')
        if Profile.objects.filter(contact__iexact=contact).exists():
            raise forms.ValidationError('An account already uses this contact.')
        return contact

    def save(self, commit=True):
        user = super().save(commit=False)
        contact = self.cleaned_data['contact']
        if '@' in contact:
            user.email = contact
        if commit:
            user.save()
            Profile.objects.create(user=user, contact=contact)
        return user


@require_http_methods(['GET', 'POST'])
def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        messages.error(request, 'The username or password you entered is incorrect.')

    return render(request, 'main/login.html')


@require_http_methods(['GET', 'POST'])
def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    form = RegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect('home')
    return render(request, 'main/register.html', {'form': form})


@login_required
def home_view(request):
    return render(request, 'main/home.html')


@require_http_methods(['POST'])
def logout_view(request):
    logout(request)
    return redirect('login')
