from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST, require_http_methods

from .forms import LoginForm, ProfileForm, SignupForm
from .models import Profile


@require_http_methods(['GET', 'POST'])
def login(request):
    next_url = request.POST.get('next') or request.GET.get('next', '')
    if request.method == 'POST':
        form = LoginForm(request.POST, request=request)
        if form.is_valid():
            form.save()
            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)
            return redirect('index')
    else:
        form = LoginForm(request=request)
    return render(request, 'core/login.html', {'form': form, 'next': next_url})


@require_http_methods(['GET', 'POST'])
def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Аккаунт успешно создан.')
            return redirect('index')
    else:
        form = SignupForm()
    return render(request, 'core/signup.html', {'form': form})


@login_required
@require_http_methods(['GET', 'POST'])
def profile(request):
    Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль обновлён.')
            return redirect('profile')
    else:
        form = ProfileForm(user=request.user)
    return render(request, 'core/profile.html', {'form': form, 'profile': request.user.profile})


@require_POST
def logout_view(request):
    next_url = request.META.get('HTTP_REFERER', '')
    auth_logout(request)
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(next_url)
    return redirect('index')


def csrf_failure(request, reason=''):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
        return JsonResponse({'error': 'CSRF-проверка не пройдена.'}, status=403)
    return render(request, 'core/403_csrf.html', status=403)
