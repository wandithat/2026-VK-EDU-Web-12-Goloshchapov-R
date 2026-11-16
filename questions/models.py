from django.conf import settings
from django.db import models
from django.db.models import (
    Case,
    Count,
    IntegerField,
    OuterRef,
    Subquery,
    Sum,
    Value,
    When,
)
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils.timesince import timesince


class Tag(models.Model):
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Название',
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class QuestionQuerySet(models.QuerySet):
    def with_page_data(self):
        likes_rating = (
            QuestionLike.objects
            .filter(question_id=OuterRef('pk'))
            .order_by()
            .values('question_id')
            .annotate(
                value=Sum(
                    Case(
                        When(is_positive=True, then=Value(1)),
                        default=Value(-1),
                        output_field=IntegerField(),
                    )
                )
            )
            .values('value')[:1]
        )
        answers_count = (
            Answer.objects
            .filter(question_id=OuterRef('pk'))
            .order_by()
            .values('question_id')
            .annotate(value=Count('pk'))
            .values('value')[:1]
        )

        return (
            self.select_related('author', 'author__profile')
            .prefetch_related('tag_objects')
            .annotate(
                rating=Coalesce(
                    Subquery(likes_rating, output_field=IntegerField()),
                    Value(0),
                    output_field=IntegerField(),
                ),
                answers_count=Coalesce(
                    Subquery(answers_count, output_field=IntegerField()),
                    Value(0),
                    output_field=IntegerField(),
                ),
            )
        )


class QuestionManager(models.Manager):
    def get_queryset(self):
        return QuestionQuerySet(self.model, using=self._db)

    def new(self):
        return self.get_queryset().with_page_data().order_by('-created_at', '-id')

    def hot(self):
        return self.get_queryset().with_page_data().order_by('-rating', '-created_at', '-id')

    def by_tag(self, tag_name):
        return (
            self.get_queryset()
            .filter(tag_objects__name=tag_name)
            .with_page_data()
            .distinct()
            .order_by('-created_at', '-id')
        )


class Question(models.Model):
    title = models.CharField(
        max_length=255,
        verbose_name='Заголовок',
    )
    text = models.TextField(verbose_name='Текст вопроса')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name='Автор',
    )
    tag_objects = models.ManyToManyField(
        Tag,
        related_name='questions',
        blank=True,
        verbose_name='Теги',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления',
    )

    objects = QuestionManager()

    class Meta:
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=['-created_at', '-id'], name='question_created_idx'),
        ]

    @property
    def tags(self):
        return [tag.name for tag in self.tag_objects.all()]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('question', kwargs={'question_id': self.pk})

    @property
    def time(self):
        return f'{timesince(self.created_at)} назад'


class AnswerQuerySet(models.QuerySet):
    def for_question(self, question):
        likes_rating = (
            AnswerLike.objects
            .filter(answer_id=OuterRef('pk'))
            .order_by()
            .values('answer_id')
            .annotate(
                value=Sum(
                    Case(
                        When(is_positive=True, then=Value(1)),
                        default=Value(-1),
                        output_field=IntegerField(),
                    )
                )
            )
            .values('value')[:1]
        )

        return (
            self.filter(question=question)
            .select_related('author', 'author__profile')
            .annotate(
                rating=Coalesce(
                    Subquery(likes_rating, output_field=IntegerField()),
                    Value(0),
                    output_field=IntegerField(),
                )
            )
            .order_by('created_at', 'id')
        )


class AnswerManager(models.Manager):
    def get_queryset(self):
        return AnswerQuerySet(self.model, using=self._db)

    def for_question(self, question):
        return self.get_queryset().for_question(question)


class Answer(models.Model):
    text = models.TextField(verbose_name='Текст ответа')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name='Автор',
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name='Вопрос',
    )
    objects = AnswerManager()
    is_correct = models.BooleanField(
        default=False,
        verbose_name='Правильный ответ',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления',
    )

    class Meta:
        verbose_name = 'Ответ'
        verbose_name_plural = 'Ответы'
        ordering = ('created_at', 'id')
        indexes = [
            models.Index(fields=['question', 'created_at', 'id'], name='answer_q_created_idx'),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['question'],
                condition=models.Q(is_correct=True),
                name='one_correct_answer_per_question',
            ),
        ]

    def __str__(self):
        return f'Ответ на вопрос №{self.question_id}'

    @property
    def correct(self):
        return self.is_correct

    @property
    def time(self):
        return f'{timesince(self.created_at)} назад'


class QuestionLike(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='question_likes',
        verbose_name='Пользователь',
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name='Вопрос',
    )
    is_positive = models.BooleanField(
        default=True,
        verbose_name='Положительная оценка',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания',
    )

    class Meta:
        verbose_name = 'Оценка вопроса'
        verbose_name_plural = 'Оценки вопросов'
        unique_together = ('user', 'question')
        indexes = [
            models.Index(fields=['question', 'is_positive'], name='q_like_rating_idx'),
        ]

    def __str__(self):
        return f'{self.user} — вопрос №{self.question_id}'


class AnswerLike(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='answer_likes',
        verbose_name='Пользователь',
    )
    answer = models.ForeignKey(
        Answer,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name='Ответ',
    )
    is_positive = models.BooleanField(
        default=True,
        verbose_name='Положительная оценка',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания',
    )

    class Meta:
        verbose_name = 'Оценка ответа'
        verbose_name_plural = 'Оценки ответов'
        unique_together = ('user', 'answer')
        indexes = [
            models.Index(fields=['answer', 'is_positive'], name='a_like_rating_idx'),
        ]

    def __str__(self):
        return f'{self.user} — ответ №{self.answer_id}'
