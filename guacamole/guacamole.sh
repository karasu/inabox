#!/bin/bash

docker stop inabox-guacd
docker rm inabox-guacd
docker run --name inabox-guacd -e GUACD_LOG_LEVEL=debug -d guacamole/guacd

docker stop inabox-guacamole
docker rm inabox-guacamole
docker run --name inabox-guacamole \
  --link inabox-guacd:guacd \
  --link postgres-db-1:postgres \
  -e POSTGRESQL_HOSTNAME=172.20.0.2 \
  -e POSTGRESQL_DATABASE=guacamole \
  -e POSTGRESQL_USER=guacamole_user \
  -e POSTGRESQL_PASSWORD=guacamole \
  -d -p 8080:8080 guacamole/guacamole
