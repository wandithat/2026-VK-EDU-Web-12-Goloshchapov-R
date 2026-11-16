from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

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


def question(request, question_id):
    current_question = get_object_or_404(Question.objects.new(), pk=question_id)
    _set_question_votes([current_question], request.user)
    page = paginate(Answer.objects.for_question(current_question), request, per_page=5)
    answers = list(page.object_list)
    answer_ids = [item.pk for item in answers]
    if request.user.is_authenticated:
        liked = set(AnswerLike.objects.filter(user=request.user, is_positive=True, answer_id__in=answer_ids).values_list('answer_id', flat=True))
        disliked = set(AnswerLike.objects.filter(user=request.user, is_positive=False, answer_id__in=answer_ids).values_list('answer_id', flat=True))
    else:
        liked, disliked = set(), set()
    for item in answers:
        item.liked = item.pk in liked
        item.disliked = item.pk in disliked
    return render(request, 'questions/question.html', {
        'question': current_question,
        'answers': answers,
        'page': page,
    })


@login_required
@require_http_methods(['GET', 'POST'])
def ask(request):
    if request.method == 'GET':
        return render(request, 'questions/ask.html')
    title = request.POST.get('title', '').strip()
    text = request.POST.get('text', '').strip()
    raw_tags = request.POST.get('tags', '')
    if not title or not text:
        messages.error(request, 'Заполните заголовок и текст вопроса.')
        return render(request, 'questions/ask.html', status=400)
    question_obj = Question.objects.create(title=title, text=text, author=request.user)
    tag_names = {name.strip().lower() for name in raw_tags.split(',') if name.strip()}
    for name in tag_names:
        tag_obj, _ = Tag.objects.get_or_create(name=name[:50])
        question_obj.tag_objects.add(tag_obj)
    messages.success(request, 'Вопрос опубликован.')
    return redirect('question', question_id=question_obj.pk)


@login_required
@require_POST
def add_answer(request, question_id):
    question_obj = get_object_or_404(Question, pk=question_id)
    text = request.POST.get('answer', '').strip()
    if not text:
        messages.error(request, 'Текст ответа не должен быть пустым.')
    else:
        Answer.objects.create(question=question_obj, author=request.user, text=text)
        messages.success(request, 'Ответ добавлен.')
    return redirect('question', question_id=question_obj.pk)


@login_required
@require_POST
def vote_question(request, question_id, value):
    question_obj = get_object_or_404(Question, pk=question_id)
    is_positive = value == 'up'
    with transaction.atomic():
        vote, created = QuestionLike.objects.get_or_create(user=request.user, question=question_obj, defaults={'is_positive': is_positive})
        if not created:
            if vote.is_positive == is_positive:
                vote.delete()
            else:
                vote.is_positive = is_positive
                vote.save(update_fields=['is_positive'])
    return redirect(question_obj.get_absolute_url())


@login_required
@require_POST
def vote_answer(request, answer_id, value):
    answer_obj = get_object_or_404(Answer.objects.select_related('question'), pk=answer_id)
    is_positive = value == 'up'
    with transaction.atomic():
        vote, created = AnswerLike.objects.get_or_create(user=request.user, answer=answer_obj, defaults={'is_positive': is_positive})
        if not created:
            if vote.is_positive == is_positive:
                vote.delete()
            else:
                vote.is_positive = is_positive
                vote.save(update_fields=['is_positive'])
    return redirect(answer_obj.question.get_absolute_url())
