from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from .models import Profile

User = get_user_model()


class ProfileInline(admin.StackedInline):
    model = Profile
    extra = 0
    max_num = 1
    fields = ('nickname', 'avatar')


class AskRomanUserAdmin(UserAdmin):
    inlines = [ProfileInline]
    list_display = (
        'username', 'email', 'first_name', 'last_name',
        'is_staff', 'is_active',
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_active', 'is_superuser')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'avatar')
    search_fields = ('user__username', 'user__email')
    list_filter = ('user__is_staff',)
    raw_id_fields = ('user',)


admin.site.unregister(User)
admin.site.register(User, AskRomanUserAdmin)
