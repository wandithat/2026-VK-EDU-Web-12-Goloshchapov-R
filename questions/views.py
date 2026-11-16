from math import ceil

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Case, IntegerField, Sum, Value, When
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST, require_http_methods

from .forms import AnswerForm, CorrectAnswerForm, QuestionForm, VoteForm
from .models import Answer, AnswerLike, Question, QuestionLike, Tag
from .pagination import paginate


def _set_question_votes(questions, user):
    ids = [item.pk for item in questions]
    if user.is_authenticated:
        liked = set(QuestionLike.objects.filter(user=user, is_positive=True, question_id__in=ids).values_list('question_id', flat=True))
        disliked = set(QuestionLike.objects.filter(user=user, is_positive=False, question_id__in=ids).values_list('question_id', flat=True))
    else:
        liked, disliked = set(), set()
    for item in questions:
        item.liked = item.pk in liked
        item.disliked = item.pk in disliked


def _set_answer_votes(answers, user):
    ids = [item.pk for item in answers]
    if user.is_authenticated:
        liked = set(AnswerLike.objects.filter(user=user, is_positive=True, answer_id__in=ids).values_list('answer_id', flat=True))
        disliked = set(AnswerLike.objects.filter(user=user, is_positive=False, answer_id__in=ids).values_list('answer_id', flat=True))
    else:
        liked, disliked = set(), set()
    for item in answers:
        item.liked = item.pk in liked
        item.disliked = item.pk in disliked


def index(request):
    page = paginate(Question.objects.new(), request)
    questions = list(page.object_list)
    _set_question_votes(questions, request.user)
    return render(request, 'questions/index.html', {'questions': questions, 'page': page})


def hot(request):
    page = paginate(Question.objects.hot(), request)
    questions = list(page.object_list)
    _set_question_votes(questions, request.user)
    return render(request, 'questions/hot.html', {'questions': questions, 'page': page})


def tag(request, tag_name):
    current_tag = get_object_or_404(Tag, name=tag_name)
    page = paginate(Question.objects.by_tag(current_tag.name), request)
    questions = list(page.object_list)
    _set_question_votes(questions, request.user)
    return render(request, 'questions/tag.html', {'questions': questions, 'page': page, 'tag_name': current_tag.name})


def _question_page(request, current_question, answer_form=None):
    _set_question_votes([current_question], request.user)
    page = paginate(Answer.objects.for_question(current_question), request, per_page=5)
    answers = list(page.object_list)
    _set_answer_votes(answers, request.user)
    return render(request, 'questions/question.html', {
        'question': current_question,
        'answers': answers,
        'page': page,
        'answer_form': answer_form or AnswerForm(),
        'can_mark_correct': request.user.is_authenticated and request.user.pk == current_question.author_id,
    })


def question(request, question_id):
    current_question = get_object_or_404(Question.objects.new(), pk=question_id)
    return _question_page(request, current_question)


@login_required
@require_http_methods(['GET', 'POST'])
def ask(request):
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question_obj = form.save(author=request.user)
            messages.success(request, 'Вопрос опубликован.')
            return redirect(question_obj.get_absolute_url())
    else:
        form = QuestionForm()
    return render(request, 'questions/ask.html', {'form': form})


@login_required
@require_POST
def add_answer(request, question_id):
    question_obj = get_object_or_404(Question, pk=question_id)
    form = AnswerForm(request.POST)
    if form.is_valid():
        answer = form.save(question=question_obj, author=request.user)
        answer_position = Answer.objects.filter(question=question_obj).count()
        page_number = ceil(answer_position / 5)
        messages.success(request, 'Ответ добавлен.')
        return redirect(f'{question_obj.get_absolute_url()}?page={page_number}#answer-{answer.pk}')
    return _question_page(request, question_obj, form)


def _ajax_auth_required(request):
    if request.user.is_authenticated:
        return None
    return JsonResponse({'error': 'Необходимо войти в аккаунт.'}, status=401)


def _vote(request, obj, model, field_name):
    form = VoteForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'error': 'Недопустимое значение оценки.'}, status=400)
    is_positive = form.cleaned_data['value'] == 'up'
    lookup = {'user': request.user, field_name: obj}
    with transaction.atomic():
        vote, created = model.objects.get_or_create(**lookup, defaults={'is_positive': is_positive})
        if not created:
            if vote.is_positive == is_positive:
                vote.delete()
            else:
                vote.is_positive = is_positive
                vote.save(update_fields=['is_positive'])
    rating = model.objects.filter(**{field_name: obj}).aggregate(
        total=Sum(
            Case(
                When(is_positive=True, then=Value(1)),
                default=Value(-1),
                output_field=IntegerField(),
            )
        )
    )['total'] or 0
    user_vote = model.objects.filter(**lookup).values_list('is_positive', flat=True).first()
    return JsonResponse({'rating': rating, 'liked': user_vote is True, 'disliked': user_vote is False})


def vote_question(request, question_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Разрешён только POST-запрос.'}, status=405)
    auth_error = _ajax_auth_required(request)
    if auth_error:
        return auth_error
    question_obj = Question.objects.filter(pk=question_id).first()
    if question_obj is None:
        return JsonResponse({'error': 'Вопрос не найден.'}, status=404)
    return _vote(request, question_obj, QuestionLike, 'question')


def vote_answer(request, answer_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Разрешён только POST-запрос.'}, status=405)
    auth_error = _ajax_auth_required(request)
    if auth_error:
        return auth_error
    answer_obj = Answer.objects.filter(pk=answer_id).first()
    if answer_obj is None:
        return JsonResponse({'error': 'Ответ не найден.'}, status=404)
    return _vote(request, answer_obj, AnswerLike, 'answer')


def mark_correct(request, question_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Разрешён только POST-запрос.'}, status=405)
    auth_error = _ajax_auth_required(request)
    if auth_error:
        return auth_error
    question_obj = Question.objects.filter(pk=question_id).first()
    if question_obj is None:
        return JsonResponse({'error': 'Вопрос не найден.'}, status=404)
    if question_obj.author_id != request.user.pk:
        return JsonResponse({'error': 'Только автор вопроса может выбрать правильный ответ.'}, status=403)
    form = CorrectAnswerForm(request.POST, question=question_obj)
    if not form.is_valid():
        return JsonResponse({'error': form.errors.as_text()}, status=400)
    with transaction.atomic():
        answer = form.save()
    return JsonResponse({'answer_id': answer.pk, 'is_correct': True})
