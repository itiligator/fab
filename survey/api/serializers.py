from rest_framework import serializers
from django.contrib.auth.models import AnonymousUser

from survey.api.models import *


__all__ = ['SurveySerializer',
           'SurveyPUTSerializer',
           'OptionSerializer',
           'QuestionPOSTSerializer',
           'QuestionGETSerializer',
           'SubmissionSerializer',
           'SubmissionPOSTSerializer']


class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ['id', 'text', 'question']

    def validate(self, data):
        if data['question'].q_type not in (Question.SELECT, Question.MULTIPLY_SELECT):
            raise serializers.ValidationError("can't add option for non-select question")
        return data


class QuestionGETSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True)

    class Meta:
        model = Question
        fields = '__all__'


class QuestionPOSTSerializer(serializers.ModelSerializer):
    # делаем создание вариантов ответа по списку из строк
    options = serializers.ListSerializer(child=serializers.CharField(), required=False)

    class Meta:
        model = Question
        fields = '__all__'

    def validate(self, data):
        if 'options' not in data and data['q_type'] in (Question.SELECT, Question.MULTIPLY_SELECT):
            raise serializers.ValidationError("can't add select question without options")
        return data

    def create(self, validated_data):
        option_texts_data = validated_data.pop('options', None)
        question = Question.objects.create(**validated_data)
        if question.q_type in (Question.SELECT, Question.MULTIPLY_SELECT):
            options = [Option(question=question, text=option_text) for option_text in option_texts_data]
            Option.objects.bulk_create(options)
        return question


class SurveySerializer(serializers.ModelSerializer):
    questions = QuestionGETSerializer(many=True)

    class Meta:
        model = Survey
        fields = '__all__'
        read_only_fields = ['created_date', 'modified_date']


class SurveyPUTSerializer(serializers.ModelSerializer):
    class Meta:
        model = Survey
        fields = '__all__'
        read_only_fields = ['created_date', 'modified_date', 'start_date']


class SelectAnswerSerializer(serializers.ModelSerializer):
    selections = serializers.SlugRelatedField(slug_field='option_id', read_only=True, many=True)

    class Meta:
        model = Answer
        fields = ['id', 'selections']


class TextAnswerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Answer
        fields = ['id', 'text']


class QuestionWithAnswersSerializer(serializers.ModelSerializer):
    question = serializers.SerializerMethodField()
    answer = serializers.SerializerMethodField()

    def get_question(self, obj):
        return QuestionGETSerializer(instance=obj).data

    def get_answer(self, obj):
        # Здесь Django по неведомой причине дёргает базу, но исключительно при положительном результате сравнения
        # Победить не удалось
        answer = next((a for a in self.context['answers'] if a.question == obj), None)

        if answer:
            if obj.q_type in (Question.SELECT, Question.MULTIPLY_SELECT):
                return SelectAnswerSerializer(instance=answer).data
            else:
                return TextAnswerSerializer(instance=answer).data
        else:
            return {}

    class Meta:
        model = Question
        fields = ['question', 'answer']


class SubmittedAnswerSerializer(serializers.ModelSerializer):
    text = serializers.CharField(required=False)
    selections = serializers.PrimaryKeyRelatedField(queryset=Option.objects, many=True, required=False)

    class Meta:
        model = Answer
        fields = ['question', 'text', 'selections']


class SubmissionSerializer(serializers.ModelSerializer):
    results = serializers.SerializerMethodField()
    url = serializers.HyperlinkedIdentityField(view_name='submission-detail', read_only=True)

    def get_results(self, obj):
        # добавляем в контекст подгруженные данные для снижения количества обращений к БД
        questions = obj.survey.questions.all()
        answers = obj.answers.all()
        return QuestionWithAnswersSerializer(
            instance=questions,
            many=True,
            context={'submission': obj, 'answers': answers}).data

    class Meta:
        model = Submission
        fields = '__all__'


class SubmissionPOSTSerializer(serializers.ModelSerializer):
    data = SubmittedAnswerSerializer(many=True, required=True, write_only=True)
    url = serializers.HyperlinkedIdentityField(view_name='submission-detail', read_only=True)

    def validate(self, data):
        # неоптимально в части запросов к БД
        survey = data['survey']
        for qa_pair in data['data']:
            try:
                question = qa_pair['question']
                if question not in survey.questions.all():
                    raise serializers.ValidationError("Question not found")
                if question.q_type in (Question.SELECT, Question.MULTIPLY_SELECT):
                    if set(qa_pair['selections']) - set(question.options.all()):
                        raise serializers.ValidationError("Selected option not found for given question")
                    if len(qa_pair['selections']) > 1 and question.q_type is Question.SELECT:
                        raise serializers.ValidationError("Can't select multiply options for single-select question")
                elif 'text' not in qa_pair:
                    raise KeyError
            except KeyError as e:
                print(e)
                raise serializers.ValidationError("Smth goes wrong with payload")
        return data

    def create(self, validated_data):
        answers_data = validated_data.pop('data')
        submission = Submission.objects.create(**validated_data)
        for answer_data in answers_data:
            if answer_data['question'].q_type in (Question.SELECT, Question.MULTIPLY_SELECT):
                answer = Answer.objects.create(question=answer_data['question'], submission=submission)
                selection = [SelectAnswer(option=selection, answer=answer) for selection in answer_data['selections']]
                SelectAnswer.objects.bulk_create(selection)
            else:
                Answer.objects.create(question=answer_data['question'], submission=submission, text=answer_data['text'])
        return submission

    class Meta:
        model = Submission
        fields = ['survey', 'data', 'url', 'user']


