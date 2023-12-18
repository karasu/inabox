from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/challenges/(?P<challenge_id>\w+)/$", consumers.SshConsumer.as_asgi()),
]
