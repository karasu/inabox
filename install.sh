#!/bin/sh

sudo pacman -S docker python-celery python-twisted python-django python-yaml \
 python-msgpack python-paramiko python-pillow redis python-redis python-six \
 python-autobahn

# Install python deps using pipman-git


pipman -S celery-progress channels channels_redis daphne django-admin-interface \
 django-bootstrap5 django-celery-beat django-celery-results django-colorfield \
 django-debug-toolbar django-minify-html django-redis minify-html \
 psycopg2-binary pycryptodome python-dateutil

#pipman -S pyyaml
