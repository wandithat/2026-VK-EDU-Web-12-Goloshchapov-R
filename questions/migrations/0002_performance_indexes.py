from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questions', '0001_initial'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='question',
            index=models.Index(fields=['-created_at', '-id'], name='question_created_idx'),
        ),
        migrations.AddIndex(
            model_name='answer',
            index=models.Index(fields=['question', 'created_at', 'id'], name='answer_q_created_idx'),
        ),
        migrations.AddIndex(
            model_name='questionlike',
            index=models.Index(fields=['question', 'is_positive'], name='q_like_rating_idx'),
        ),
        migrations.AddIndex(
            model_name='answerlike',
            index=models.Index(fields=['answer', 'is_positive'], name='a_like_rating_idx'),
        ),
    ]
