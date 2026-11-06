from django.http import Http404
from django.shortcuts import render
from .pagination import paginate

AUTHORS = ['Mr. Freeman', 'Dr. House', 'Bender', 'Queen Victoria', 'V. Pupkin']

QUESTIONS = []

for i in range(1, 31):
    QUESTIONS.append({
        'id': i,
        'title': f'Тестовый вопрос №{i}',
        'text': f'Это описание тестового вопроса номер {i}.',
        'rating': 30 - i,
        'author': 'Roman',
        'time': f'{i} часов назад',
        'answers_count': i % 10 + 1,
        'tags': ['python', 'django'] if i % 2 == 0 else ['html', 'css'],
    })


def index(request):
    page = paginate(QUESTIONS, request)

    return render(request, 'questions/index.html', {
        'questions': page.object_list,
        'page': page,
    })

def hot(request):
    popular_questions = sorted(
        QUESTIONS,
        key=lambda question: question['rating'],
        reverse=True
    )

    page = paginate(popular_questions, request)

    return render(request, 'questions/hot.html', {
        'questions': page.object_list,
        'page': page,
    })


def tag(request, tag_name):
    tagged_questions = [
        question for question in QUESTIONS
        if tag_name in question['tags']
    ]

    page = paginate(tagged_questions, request)

    return render(request, 'questions/tag.html', {
        'questions': page.object_list,
        'page': page,
        'tag_name': tag_name,
    })


def question(request, question_id):
    current_question = next(
        (q for q in QUESTIONS if q['id'] == question_id),
        None
    )

    if current_question is None:
        raise Http404('Вопрос не найден')

    all_answers = []
    for i in range(1, 8):
        all_answers.append({
            'author': AUTHORS[i % len(AUTHORS)],
            'text': f'Пример ответа №{i} на этот вопрос.',
            'rating': 10 - i,
            'liked': i == 1,
            'disliked': i == 2,
            'correct': i == 1,
        })

    page = paginate(all_answers, request, per_page=5)

    return render(request, 'questions/question.html', {
        'question': current_question,
        'answers': page.object_list,
        'page': page,
    })


def ask(request):
    return render(request, 'questions/ask.html')