FROM alpine:latest

WORKDIR /app

RUN set -xe;

COPY . .

RUN apk add --no-cache python3 py3-pip tini; \
    pip install --upgrade pip setuptools-scm; \
    python3 setup.py install; \
    python3 manage.py makemigrations; \
    python3 manage.py migrate; \
    addgroup -g 1000 inabox; \
    adduser -u 1000 -G inabox -D -h /app inabox; \
    chown -R inabox:inabox /app

USER inabox
EXPOSE 8000/tcp
ENTRYPOINT [ "tini", "--" ]
CMD [ "python3", "/app/manage.py", "runserver", "0.0.0.0:8000" ]

