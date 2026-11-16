from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from .models import Answer, AnswerLike, Question, QuestionLike, Tag


class QuestionPagesTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='tester',
            password='test-password',
        )
        self.tag = Tag.objects.create(name='python')
        self.question = Question.objects.create(
            title='Как работает Django?',
            text='Текст вопроса',
            author=self.user,
        )
        self.question.tag_objects.add(self.tag)
        self.answer = Answer.objects.create(
            question=self.question,
            author=self.user,
            text='Текст ответа',
        )

    def test_question_pages_return_success(self):
        for url in (
            reverse('index'),
            reverse('hot'),
            reverse('tag', args=('python',)),
            reverse('question', args=(self.question.pk,)),
        ):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_missing_question_returns_404(self):
        self.assertEqual(self.client.get('/question/999999/').status_code, 404)

    def test_missing_tag_returns_404(self):
        self.assertEqual(self.client.get('/tag/missing/').status_code, 404)

    def test_empty_database_state_is_rendered(self):
        Question.objects.all().delete()
        response = self.client.get(reverse('index'))
        self.assertContains(response, 'Пока нет вопросов.')

    def test_question_like_is_unique_per_user(self):
        QuestionLike.objects.create(user=self.user, question=self.question)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                QuestionLike.objects.create(user=self.user, question=self.question)

    def test_answer_like_is_unique_per_user(self):
        AnswerLike.objects.create(user=self.user, answer=self.answer)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                AnswerLike.objects.create(user=self.user, answer=self.answer)

    def test_question_page_data_uses_correct_rating_and_answer_count(self):
        second_user = get_user_model().objects.create_user(
            username='second-tester',
            password='test-password',
        )
        QuestionLike.objects.create(user=self.user, question=self.question, is_positive=True)
        QuestionLike.objects.create(user=second_user, question=self.question, is_positive=False)

        question = Question.objects.new().get(pk=self.question.pk)

        self.assertEqual(question.rating, 0)
        self.assertEqual(question.answers_count, 1)

    def test_question_page_data_returns_zero_for_empty_relations(self):
        question = Question.objects.create(
            title='Без ответов и оценок',
            text='Текст',
            author=self.user,
        )

        question = Question.objects.new().get(pk=question.pk)

        self.assertEqual(question.rating, 0)
        self.assertEqual(question.answers_count, 0)

    def test_answer_rating_is_calculated_correctly(self):
        second_user = get_user_model().objects.create_user(
            username='second-answer-tester',
            password='test-password',
        )
        AnswerLike.objects.create(user=self.user, answer=self.answer, is_positive=True)
        AnswerLike.objects.create(user=second_user, answer=self.answer, is_positive=False)

        answer = Answer.objects.for_question(self.question).get(pk=self.answer.pk)

        self.assertEqual(answer.rating, 0)


class QuestionActionsTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='action-user', password='test-password')
        self.other_user = get_user_model().objects.create_user(username='other-user', password='test-password')
        self.question = Question.objects.create(title='Вопрос', text='Описание', author=self.other_user)
        self.answer = Answer.objects.create(question=self.question, author=self.other_user, text='Ответ')
        self.client.force_login(self.user)

    def test_authenticated_user_can_create_question(self):
        response = self.client.post(reverse('ask'), {'title': 'Новый вопрос', 'text': 'Текст', 'tags': 'python, django'})
        created = Question.objects.get(title='Новый вопрос')
        self.assertRedirects(response, reverse('question', args=(created.pk,)))
        self.assertEqual(set(created.tags), {'python', 'django'})

    def test_authenticated_user_can_add_answer(self):
        response = self.client.post(reverse('add_answer', args=(self.question.pk,)), {'answer': 'Мой ответ'})
        self.assertRedirects(response, reverse('question', args=(self.question.pk,)))
        self.assertTrue(Answer.objects.filter(question=self.question, author=self.user, text='Мой ответ').exists())

    def test_question_vote_can_be_added_changed_and_removed(self):
        url = reverse('vote_question', args=(self.question.pk, 'up'))
        self.client.post(url)
        vote = QuestionLike.objects.get(user=self.user, question=self.question)
        self.assertTrue(vote.is_positive)
        self.client.post(reverse('vote_question', args=(self.question.pk, 'down')))
        vote.refresh_from_db()
        self.assertFalse(vote.is_positive)
        self.client.post(reverse('vote_question', args=(self.question.pk, 'down')))
        self.assertFalse(QuestionLike.objects.filter(user=self.user, question=self.question).exists())

    def test_answer_vote_can_be_added(self):
        response = self.client.post(reverse('vote_answer', args=(self.answer.pk, 'up')))
        self.assertRedirects(response, reverse('question', args=(self.question.pk,)))
        self.assertTrue(AnswerLike.objects.filter(user=self.user, answer=self.answer, is_positive=True).exists())

    def test_anonymous_user_cannot_create_question(self):
        self.client.logout()
        response = self.client.post(reverse('ask'), {'title': 'Вопрос', 'text': 'Текст'})
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('ask')}")
