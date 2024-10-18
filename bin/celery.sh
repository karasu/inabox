#!/bin/bash
INABOX_DIR="/home/karasu/inabox"
BIN_DIR="${INABOX_DIR}/bin"
SRC_DIR="${INABOX_DIR}/src"

source ${BIN_DIR}/activate
cd ${SRC_DIR}
celery $@

