import random
from itertools import islice

from faker import Faker

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.models import Profile
from questions.models import Answer, AnswerLike, Question, QuestionLike, Tag


BATCH_SIZE = 5000


def batches(iterable, size=BATCH_SIZE):
    iterator = iter(iterable)
    while batch := list(islice(iterator, size)):
        yield batch


class Command(BaseCommand):
    help = 'Заполняет БД тестовыми данными. Формат: fill_db [ratio].'

    def add_arguments(self, parser):
        parser.add_argument('ratio', type=int)

    @transaction.atomic
    def handle(self, *args, **options):
        ratio = options['ratio']
        if ratio < 2:
            raise CommandError('ratio должен быть не меньше 2: при ratio=1 недостаточно уникальных пар для 200 оценок.')

        User = get_user_model()

        user_count = ratio
        question_count = ratio * 10
        answer_count = ratio * 100
        tag_count = ratio
        total_likes = ratio * 200

        username_prefix = f'seed_{ratio}_'
        tag_prefix = f'seed_{ratio}_'

        if User.objects.filter(username__startswith=username_prefix).exists():
            raise CommandError(
                f'Данные для ratio={ratio} уже существуют. '
                'Удалите тестовые записи с префиксом '
                f'{username_prefix} перед повторным запуском.'
            )
        if Tag.objects.filter(name__startswith=tag_prefix).exists():
            raise CommandError(
                f'Теги для ratio={ratio} уже существуют. '
                'Удалите их перед повторным запуском.'
            )

        fake = Faker('ru_RU')
        rng = random.Random()

        self.stdout.write('1/6 Создание пользователей...')
        password = make_password(None)
        users = (
            User(
                username=f'{username_prefix}{i}',
                email=f'seed_{ratio}_{i}@example.test',
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                password=password,
            )
            for i in range(user_count)
        )
        user_ids = []
        for batch in batches(users):
            User.objects.bulk_create(batch, batch_size=BATCH_SIZE)
            user_ids.extend(user.pk for user in batch)

        profiles = (Profile(user_id=user_id) for user_id in user_ids)
        for batch in batches(profiles):
            Profile.objects.bulk_create(batch, batch_size=BATCH_SIZE)

        self.stdout.write('2/6 Создание тегов...')
        tags = (
            Tag(name=f'{tag_prefix}{i}')
            for i in range(tag_count)
        )
        tag_ids = []
        for batch in batches(tags):
            Tag.objects.bulk_create(batch, batch_size=BATCH_SIZE)
            tag_ids.extend(tag.pk for tag in batch)

        self.stdout.write('3/6 Создание вопросов...')
        questions = (
            Question(
                title=fake.sentence(nb_words=7),
                text=fake.paragraph(nb_sentences=4),
                author_id=rng.choice(user_ids),
            )
            for _ in range(question_count)
        )
        question_ids = []
        for batch in batches(questions):
            Question.objects.bulk_create(batch, batch_size=BATCH_SIZE)
            question_ids.extend(question.pk for question in batch)

        self.stdout.write('4/6 Привязка тегов и создание ответов...')
        through = Question.tag_objects.through

        def make_tag_links():
            for question_id in question_ids:
                count = min(rng.randint(1, 3), len(tag_ids))
                for tag_id in rng.sample(tag_ids, count):
                    yield through(question_id=question_id, tag_id=tag_id)

        for batch in batches(make_tag_links()):
            through.objects.bulk_create(
                batch,
                batch_size=BATCH_SIZE,
                ignore_conflicts=True,
            )

        answers = (
            Answer(
                question_id=rng.choice(question_ids),
                author_id=rng.choice(user_ids),
                text=fake.paragraph(nb_sentences=3),
                is_correct=False,
            )
            for _ in range(answer_count)
        )
        answer_ids = []
        for batch in batches(answers):
            Answer.objects.bulk_create(batch, batch_size=BATCH_SIZE)
            answer_ids.extend(answer.pk for answer in batch)

        self.stdout.write('5/6 Создание оценок...')
        # Для каждой оценки назначается уникальная пара user/object.
        # При ratio >= 2 суммарной ёмкости пар хватает на ratio * 200 оценок.
        question_likes_count = min(
            total_likes // 2,
            user_count * question_count,
        )
        answer_likes_count = total_likes - question_likes_count

        def question_likes():
            for i in range(question_likes_count):
                yield QuestionLike(
                    user_id=user_ids[i % user_count],
                    question_id=question_ids[i // user_count],
                    is_positive=bool(rng.getrandbits(1)),
                )

        def answer_likes():
            for i in range(answer_likes_count):
                yield AnswerLike(
                    user_id=user_ids[i % user_count],
                    answer_id=answer_ids[i // user_count],
                    is_positive=bool(rng.getrandbits(1)),
                )

        for batch in batches(question_likes()):
            QuestionLike.objects.bulk_create(batch, batch_size=BATCH_SIZE)
        for batch in batches(answer_likes()):
            AnswerLike.objects.bulk_create(batch, batch_size=BATCH_SIZE)

        self.stdout.write('6/6 Проверка количества созданных записей...')
        self.stdout.write(self.style.SUCCESS(
            'Заполнение завершено: '
            f'пользователи={user_count}, '
            f'вопросы={question_count}, '
            f'ответы={answer_count}, '
            f'теги={tag_count}, '
            f'оценки={total_likes}.'
        ))
