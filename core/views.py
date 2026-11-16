from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from .models import Profile


@require_http_methods(['GET', 'POST'])
def login(request):
    if request.method == 'POST':
        username = request.POST.get('login', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('index')
        messages.error(request, 'Неверный логин или пароль.')
    return render(request, 'core/login.html')


@require_http_methods(['GET', 'POST'])
def signup(request):
    if request.method == 'POST':
        username = request.POST.get('login', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password_repeat = request.POST.get('password_repeat', '')
        if not username or not email or not password:
            messages.error(request, 'Заполните все обязательные поля.')
        elif password != password_repeat:
            messages.error(request, 'Пароли не совпадают.')
        elif User.objects.filter(username__iexact=username).exists():
            messages.error(request, 'Пользователь с таким логином уже существует.')
        elif User.objects.filter(email__iexact=email).exists():
            messages.error(request, 'Пользователь с такой почтой уже существует.')
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            Profile.objects.get_or_create(user=user)
            auth_login(request, user)
            messages.success(request, 'Аккаунт успешно создан.')
            return redirect('index')
    return render(request, 'core/signup.html')


@login_required
@require_http_methods(['GET', 'POST'])
def profile(request):
    profile_obj, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        username = request.POST.get('login', '').strip()
        email = request.POST.get('email', '').strip()
        if not username or not email:
            messages.error(request, 'Логин и почта не должны быть пустыми.')
        elif User.objects.exclude(pk=request.user.pk).filter(username__iexact=username).exists():
            messages.error(request, 'Этот логин уже занят.')
        elif User.objects.exclude(pk=request.user.pk).filter(email__iexact=email).exists():
            messages.error(request, 'Эта почта уже используется.')
        else:
            request.user.username = username
            request.user.email = email
            request.user.save(update_fields=['username', 'email'])
            if request.FILES.get('avatar'):
                profile_obj.avatar = request.FILES['avatar']
                profile_obj.save(update_fields=['avatar'])
            messages.success(request, 'Профиль обновлён.')
            return redirect('profile')
    return render(request, 'core/profile.html', {'profile': profile_obj})


@require_POST
def logout_view(request):
    auth_logout(request)
    return redirect('index')
