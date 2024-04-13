ARG PYTHON_VERSION=3.11.7-alpine
FROM python:${PYTHON_VERSION} as base

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

ENV DJANGO_DEBUG=False

WORKDIR /app

# Create a non-privileged user that the app will run under.
# See https://docs.docker.com/go/dockerfile-user-best-practices/
ARG UID=10001
RUN adduser --disabled-password --gecos "" --home "/app" \
    --shell "/sbin/nologin" --no-create-home --uid "${UID}" \
    inabox

# Install python-ldap dependencies (and celery and supervisor)
#RUN apt-get update && apt-get -y install build-essential python3-dev \
#    libldap2-dev libsasl2-dev slapd ldap-utils tox \
#    lcov valgrind celery supervisor
RUN apk add build-base openldap-dev python3-dev rust cargo \
    celery supervisor 

# minify-html takes forever to build. Let's use a prebuilt file here
RUN --mount=type=bind,source=services/inabox/minify_html-0.15.0-cp311-cp311-linux_x86_64.whl,target=minify_html-0.15.0-cp311-cp311-linux_x86_64.whl \
    python -m pip install minify_html-0.15.0-cp311-cp311-linux_x86_64.whl --break-system-packages

# Download dependencies as a separate step to take advantage of Docker's caching.
# Leverage a cache mount to /root/.cache/pip to speed up subsequent builds.
# Leverage a bind mount to requirements.txt to avoid having to copy them into
# this layer.
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=../../requirements.txt,target=requirements.txt \
    python -m pip install -r requirements.txt --break-system-packages

# Copy the app source code into the container.
COPY src/. .

# Remove cached migration files
RUN rm -f app/migrations/*.py
RUN rm -rf app/migrations/__pycache__
 
# Install supervisord (it will run Daphne and Celery)
RUN mkdir -p /run/daphne /etc/supervisor/conf.d
ADD services/inabox/supervisord.conf /etc/supervisor
ADD services/inabox/inaboxd.conf /etc/supervisor/conf.d/
ADD services/inabox/celeryd.conf /etc/supervisor/conf.d/
ADD services/inabox/celerybeatd.conf /etc/supervisor/conf.d/

# Expose the port that the application listens on.
EXPOSE 8000

RUN rm -rf static && python manage.py collectstatic

# Prepare django database and run supervisor
CMD python manage.py makemigrations app; \
    python manage.py migrate; \
    python manage.py loaddata app/classgroups app/users app/challenges app/quests app/news; \
    /usr/bin/supervisord -c /etc/supervisor/supervisord.conf
