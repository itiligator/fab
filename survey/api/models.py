import datetime

from django.contrib.auth.models import User
from django.db import models

DEFAULT_LENGTH = 140

__all__ = ['Survey',
           'Question',
           'Option',
           'Submission',
           'Answer',
           'SelectAnswer']


class BaseModel(models.Model):
    """Расширяет models.Model за счет добавления даты создания и даты изменения"""

    created_date: datetime.datetime = models.DateTimeField(auto_now_add=True)
    """Дата создания"""
    modified_date: datetime.datetime = models.DateTimeField(auto_now=True)
    """Дата изменения"""

    class Meta:
        abstract = True


class Survey(BaseModel):
    """Опрос"""

    title: str = models.CharField(max_length=DEFAULT_LENGTH)
    """Наименование"""
    start_date: datetime.datetime = models.DateField()
    """Дата начала проведения"""
    end_date: datetime.datetime = models.DateField()
    """Дата окончания проведения"""
    description: str = models.CharField(max_length=DEFAULT_LENGTH, blank=True)
    """Описание"""

    def __str__(self):
        return '%s' % self.title


class Question(BaseModel):
    """Базовый класс вопросов"""
    TEXT = 0
    SELECT = 1
    MULTIPLY_SELECT = 2

    QUESTION_TYPES = (
        (TEXT, 'Text'),
        (SELECT, 'Select'),
        (MULTIPLY_SELECT, 'Multiply select')
    )

    title: str = models.CharField(max_length=DEFAULT_LENGTH)
    """Содержание вопроса"""
    survey: Survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name="questions",)
    """Опрос, в котором задается вопрос"""
    q_type: int = models.IntegerField(default=TEXT, choices=QUESTION_TYPES)
    """Тип вопроса"""

    def __str__(self):
        return '%s' % self.title


class Option(BaseModel):
    """Вариант ответа на вопрос с выбором варианта"""

    question: Question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    """Вопрос, для которого дан вариант ответа"""
    text: str = models.CharField(max_length=DEFAULT_LENGTH)
    """Текст варианта ответа"""

    def __str__(self):
        return '%s' % self.text


class Submission(BaseModel):
    """Набор ответов на вопросы из опроса"""

    survey: Survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='submissions')
    """Опрос для которого дан набор ответов"""
    user: User = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='submissions')
    """Пользователь, который сформировал набор ответов (допускается анонимное участие в опросе)"""

    def __str__(self):
        return 'Submission for "%s" from "%s" user' % (self.survey, self.user)


class Answer(BaseModel):
    """Базовый класс ответа"""

    question: Question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    """Вопрос на который дан ответ"""
    submission: Submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='answers')
    """Набор ответов, в котором содержится данный ответ"""
    text: str = models.CharField(max_length=DEFAULT_LENGTH, blank=True)
    """Текст ответа"""

    class Meta:
        unique_together = [['question', 'submission']]

    def __str__(self):
        return 'Answer for "%s" question in %s' % (self.question, self.submission)


class SelectAnswer(BaseModel):
    """Выбранный вариант ответа"""

    answer: Answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name='selections')
    """Ответ, по которому группируются варинаты"""
    option: Option = models.ForeignKey(Option, on_delete=models.CASCADE, related_name='selections')
    """Выбранная при ответе опция"""

    class Meta:
        unique_together = [['answer', 'option']]

    def __str__(self):
        return 'Selected "%s" option for "%s" answer' % (self.option, self.answer)
