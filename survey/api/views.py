import datetime

from survey.api.models import *
from rest_framework import viewsets
from rest_framework import permissions
from survey.api.serializers import *
import django_filters.rest_framework


class SurveyViewSet(viewsets.ModelViewSet):
    queryset = Survey.objects.all()
    serializer_class = SurveySerializer

    def get_queryset(self):
        queryset = self.queryset
        # костыль для получения активных опросов
        # хотел было прикрутить фильтр по "вычисляемому" полю (вроде hybrid property из sqlalchemy и peewee),
        # но не нашел способа сделать это элегантно
        active = self.request.query_params.get('active')
        if active == '1':
            queryset = queryset.filter(end_date__gte=datetime.datetime.now(), start_date__lte=datetime.datetime.now())
        elif active == '0':
            queryset = (queryset.filter(end_date__lte=datetime.datetime.now())
                        | queryset.filter(start_date__gte=datetime.datetime.now()))
        return queryset

    def get_serializer_class(self):
        serializer_class = self.serializer_class
        # запрещаем обновление даты начала опроса
        if self.request.method == 'PUT':
            serializer_class = SurveyPUTSerializer
        return serializer_class

    def get_permissions(self):
        if self.request.method in ('POST', 'PUT', 'DELETE'):
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]


class OptionViewSet(viewsets.ModelViewSet):
    queryset = Option.objects.all()
    serializer_class = OptionSerializer

    def get_permissions(self):
        return [permissions.IsAdminUser()]


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all().prefetch_related('options')
    serializer_class = QuestionGETSerializer

    def get_serializer_class(self):
        serializer_class = self.serializer_class
        # прикручиваем фичу с созданием вариантов ответа по списку строк
        if self.request.method == 'POST':
            serializer_class = QuestionPOSTSerializer
        return serializer_class

    def get_permissions(self):
        return [permissions.IsAdminUser()]


class SubmissionViewSet(viewsets.ModelViewSet):
    # подгружаем необходимые дочерние элементы
    queryset = Submission.objects.all().prefetch_related('answers',
                                                         'answers__selections',
                                                         'survey',
                                                         'survey__questions',
                                                         'survey__questions__options')
    serializer_class = SubmissionSerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_fields = ['user']

    def get_serializer_class(self):
        serializer_class = self.serializer_class
        if self.request.method == 'POST':
            serializer_class = SubmissionPOSTSerializer
        return serializer_class

    def get_permissions(self):
        if self.request.method in ('PUT', 'DELETE'):
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

