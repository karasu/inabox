from django.contrib import admin

# Register your models here.

from .models import Challenge
from .models import User
from .models import DockerImage
from .models import Area

admin.site.register(Challenge)
admin.site.register(Area)
admin.site.register(User)
admin.site.register(DockerImage)
