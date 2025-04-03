FROM python:3.13-bullseye

#RUN set -eux; \
#    rm -f /etc/apt/apt.conf.d/docker-clean; \
#    echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache;
#RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
#    --mount=type=cache,target=/var/lib/apt,sharing=locked \
#    apt-get update \
#    && apt-get install -y gettext binutils libproj-dev gdal-bin

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
