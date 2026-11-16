from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('questions', '0002_performance_indexes'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='answer',
            constraint=models.UniqueConstraint(
                fields=('question',),
                condition=models.Q(is_correct=True),
                name='one_correct_answer_per_question',
            ),
        ),
    ]
