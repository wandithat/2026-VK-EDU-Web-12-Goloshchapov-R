from django import forms
from django.core.exceptions import ValidationError

from .models import Answer, Question, Tag


class QuestionForm(forms.ModelForm):
    tags = forms.CharField(
        label='Tags',
        required=False,
        max_length=260,
        help_text='Через запятую, не более 5 тегов.',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    class Meta:
        model = Question
        fields = ('title', 'text')
        widgets = {
            'title': forms.TextInput(attrs={'maxlength': 255}),
            'text': forms.Textarea(attrs={'rows': 5}),
        }

    def clean_tags(self):
        names = list(dict.fromkeys(
            name.strip().lower()
            for name in self.cleaned_data['tags'].split(',')
            if name.strip()
        ))
        if len(names) > 5:
            raise ValidationError('Можно указать не более 5 тегов.')
        if any(len(name) > 50 for name in names):
            raise ValidationError('Длина каждого тега не должна превышать 50 символов.')
        return names

    def save(self, commit=True, author=None):
        question = super().save(commit=False)
        if author is not None:
            question.author = author
        if commit:
            question.save()
            tags = [Tag.objects.get_or_create(name=name)[0] for name in self.cleaned_data['tags']]
            question.tag_objects.set(tags)
            self.save_m2m()
        return question


class AnswerForm(forms.ModelForm):
    text = forms.CharField(
        max_length=2000,
        widget=forms.Textarea(attrs={'rows': 4, 'maxlength': 2000}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].widget.attrs['class'] = 'form-control'

    class Meta:
        model = Answer
        fields = ('text',)
        widgets = {
            'text': forms.Textarea(attrs={'rows': 4, 'maxlength': 2000}),
        }

    def save(self, commit=True, question=None, author=None):
        answer = super().save(commit=False)
        if question is not None:
            answer.question = question
        if author is not None:
            answer.author = author
        if commit:
            answer.save()
            self.save_m2m()
        return answer


class VoteForm(forms.Form):
    value = forms.ChoiceField(choices=(('up', 'Like'), ('down', 'Dislike')))


class CorrectAnswerForm(forms.Form):
    answer_id = forms.IntegerField(min_value=1)

    def __init__(self, *args, question, **kwargs):
        self.question = question
        super().__init__(*args, **kwargs)

    def clean_answer_id(self):
        answer_id = self.cleaned_data['answer_id']
        if not Answer.objects.filter(pk=answer_id, question=self.question).exists():
            raise ValidationError('Ответ не относится к этому вопросу.')
        return answer_id

    def save(self):
        answer = Answer.objects.get(pk=self.cleaned_data['answer_id'], question=self.question)
        Answer.objects.filter(question=self.question).update(is_correct=False)
        answer.is_correct = True
        answer.save(update_fields=['is_correct'])
        return answer
