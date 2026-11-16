from pathlib import Path
from uuid import uuid4

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models


MAX_AVATAR_SIZE = 2 * 1024 * 1024


def validate_avatar_size(image):
    if image.size > MAX_AVATAR_SIZE:
        raise ValidationError('Размер аватара не должен превышать 2 МБ.')


def avatar_upload_to(instance, filename):
    extension = Path(filename).suffix.lower()
    return f'avatars/{uuid4().hex}{extension}'


class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Пользователь',
    )
    nickname = models.CharField(
        max_length=80,
        blank=True,
        verbose_name='Никнейм',
    )
    avatar = models.ImageField(
        upload_to=avatar_upload_to,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp']),
            validate_avatar_size,
        ],
        blank=True,
        null=True,
        verbose_name='Аватар',
    )

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

    def __str__(self):
        return self.nickname or self.user.username
