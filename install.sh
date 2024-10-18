#!/bin/sh
INSTALL_DIR="/home/karasu/inabox"

if [ -f /usr/bin/apt ]; then
  sudo apt -y install docker-ce docker-compose-plugin celery redis
  sudo apt -y install python3-pip python3-venv python3-full
elif [ -f /usr/bin/pacman ]; then
  sudo pacman -S --noconfirm docker redis
  sudo pacman -S --noconfirm python-pip python3
else
  echo Distro not supported.
fi 

python3 -m venv ${INSTALL_DIR}

PYTHON_BIN="${INSTALL_DIR}/bin/python"
PIP_BIN="${INSTALL_DIR}/bin/pip"

${PIP_BIN} install channels django daphne docker django-admin-interface \
  django-bootstrap5 django-minify-html minify-html celery twisted pyyaml \
  msgpack paramiko pillow redis six autobahn celery-progress \
  django-celery-beat django-celery-results django-colorfield \
  django-debug-toolbar channels-redis redis django-redis pycryptodome \
  python-dateutil psycopg2-binary daphne

# django-channels
