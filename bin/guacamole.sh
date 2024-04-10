#!/bin/bash

sudo systemctl stop systemd-resolved
docker-compose down
docker-compose up coredns proxy guacamole

