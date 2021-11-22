FROM python:3.10.0-alpine

ENV PYTHONUNBUFFERED 1

RUN mkdir /survey_service

WORKDIR /survey_service

ADD . /survey_service/

RUN pip install -r requirements.txt

EXPOSE 8080

CMD python manage.py runserver 0.0.0.0:8080

# docker build -t fab .
# docker run -d -p 8080:8080 fab
