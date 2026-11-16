import core.models
from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='nickname',
            field=models.CharField(blank=True, max_length=80, verbose_name='Никнейм'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='avatar',
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to=core.models.avatar_upload_to,
                validators=[
                    django.core.validators.FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp']),
                    core.models.validate_avatar_size,
                ],
                verbose_name='Аватар',
            ),
        ),
    ]
