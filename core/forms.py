from django import forms
from django.contrib.auth import authenticate, get_user_model, login as auth_login
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import Profile

User = get_user_model()


class LoginForm(forms.Form):
    login = forms.CharField(label='Login', max_length=150)
    password = forms.CharField(label='Password', widget=forms.PasswordInput)

    def __init__(self, *args, request=None, **kwargs):
        self.request = request
        self.user = None
        super().__init__(*args, **kwargs)
        self.fields['login'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Enter your login here'})
        self.fields['password'].widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('login')
        password = cleaned_data.get('password')
        if username and password:
            self.user = authenticate(
                self.request,
                username=username.strip(),
                password=password,
            )
            if self.user is None:
                raise ValidationError('Неверный логин или пароль.')
        return cleaned_data

    def save(self):
        auth_login(self.request, self.user)
        return self.user


class SignupForm(forms.Form):
    login = forms.CharField(label='Login', max_length=150)
    email = forms.EmailField(label='Email')
    name = forms.CharField(label='Name', max_length=150)
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    password_repeat = forms.CharField(label='Repeat password', widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def clean_login(self):
        login = self.cleaned_data['login'].strip()
        if User.objects.filter(username__iexact=login).exists():
            raise ValidationError('Пользователь с таким логином уже существует.')
        return login

    def clean_email(self):
        email = self.cleaned_data['email'].strip()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('Пользователь с такой почтой уже существует.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_repeat = cleaned_data.get('password_repeat')
        if password and password_repeat and password != password_repeat:
            self.add_error('password_repeat', 'Пароли не совпадают.')
        if password:
            user = User(
                username=cleaned_data.get('login', ''),
                email=cleaned_data.get('email', ''),
                first_name=cleaned_data.get('name', ''),
            )
            try:
                validate_password(password, user=user)
            except ValidationError as error:
                self.add_error('password', error)
        return cleaned_data

    def save(self):
        user = User.objects.create_user(
            username=self.cleaned_data['login'],
            email=self.cleaned_data['email'],
            first_name=self.cleaned_data['name'],
            password=self.cleaned_data['password'],
        )
        Profile.objects.update_or_create(
            user=user,
            defaults={'nickname': self.cleaned_data['name']},
        )
        return user


class ProfileForm(forms.ModelForm):
    login = forms.CharField(label='Login', max_length=150)
    email = forms.EmailField(label='Email')
    name = forms.CharField(label='Name', max_length=150, required=False)

    class Meta:
        model = Profile
        fields = ('nickname', 'avatar')
        widgets = {
            'nickname': forms.TextInput(attrs={'maxlength': 80}),
            'avatar': forms.ClearableFileInput(attrs={'accept': '.jpg,.jpeg,.png,.webp'}),
        }

    def __init__(self, *args, user, **kwargs):
        self.user = user
        kwargs.setdefault('instance', user.profile)
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.fields['login'].initial = user.username
            self.fields['email'].initial = user.email
            self.fields['name'].initial = user.first_name
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def clean_login(self):
        login = self.cleaned_data['login'].strip()
        if User.objects.exclude(pk=self.user.pk).filter(username__iexact=login).exists():
            raise ValidationError('Этот логин уже занят.')
        return login

    def clean_email(self):
        email = self.cleaned_data['email'].strip()
        if User.objects.exclude(pk=self.user.pk).filter(email__iexact=email).exists():
            raise ValidationError('Эта почта уже используется.')
        return email

    def save(self, commit=True):
        profile = super().save(commit=False)
        self.user.username = self.cleaned_data['login']
        self.user.email = self.cleaned_data['email']
        self.user.first_name = self.cleaned_data['name']
        if commit:
            self.user.save(update_fields=['username', 'email', 'first_name'])
            profile.user = self.user
            profile.save()
            self.save_m2m()
        return profile
