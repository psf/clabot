FROM python:3.13-alpine

RUN apk add --no-cache bash

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
RUN mkdir /code
WORKDIR /code
COPY requirements.txt /tmp/requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r /tmp/requirements.txt

COPY . /code/
RUN \
    DJANGO_SECRET_KEY=deadbeefcafe \
    DATABASE_URL=postgres:///db \
    DJANGO_SETTINGS_MODULE=clabot.settings \
    python manage.py collectstatic --noinput
