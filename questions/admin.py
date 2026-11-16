from django.contrib import admin
from django.db.models import Count
from django.contrib.admin import SimpleListFilter

from .models import Answer, AnswerLike, Question, QuestionLike, Tag


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    raw_id_fields = ('author',)
    fields = ('author', 'text', 'is_correct', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'author', 'created_at', 'answers_total')
    search_fields = ('title', 'text', 'author__username')
    list_filter = ('created_at',)
    raw_id_fields = ('author', 'tag_objects')
    inlines = (AnswerInline,)
    date_hierarchy = 'created_at'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('author').annotate(
            _answers_total=Count('answers', distinct=True)
        )

    @admin.display(description='Количество ответов', ordering='_answers_total')
    def answers_total(self, obj):
        return obj._answers_total


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'author', 'is_correct', 'created_at')
    search_fields = ('text', 'author__username', 'question__title')
    list_filter = ('is_correct', 'created_at')
    raw_id_fields = ('question', 'author')
    date_hierarchy = 'created_at'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('question', 'author')


class TagInitialFilter(SimpleListFilter):
    title = 'Первая буква'
    parameter_name = 'initial'

    def lookups(self, request, model_admin):
        return [(letter, letter.upper()) for letter in 'abcdefghijklmnopqrstuvwxyzабвгдежзийклмнопрстуфхцчшщыэюя']

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(name__istartswith=self.value())
        return queryset


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'questions_total')
    search_fields = ('name',)
    list_filter = (TagInitialFilter,)
    ordering = ('name',)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _questions_total=Count('questions', distinct=True)
        )

    @admin.display(description='Количество вопросов', ordering='_questions_total')
    def questions_total(self, obj):
        return obj._questions_total


@admin.register(QuestionLike)
class QuestionLikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'question', 'is_positive', 'created_at')
    search_fields = ('user__username', 'question__title')
    list_filter = ('is_positive', 'created_at')
    raw_id_fields = ('user', 'question')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'question')


@admin.register(AnswerLike)
class AnswerLikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'answer', 'is_positive', 'created_at')
    search_fields = ('user__username', 'answer__text')
    list_filter = ('is_positive', 'created_at')
    raw_id_fields = ('user', 'answer')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'answer')
