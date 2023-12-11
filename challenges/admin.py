from django.contrib import admin

# Register your models here.

from .models import Challenge
from .models import Person
from .models import DockerImage
from .models import DockerContainer
from .models import Area
from .models import ClassGroup

admin.site.register(Challenge)
admin.site.register(Area)
admin.site.register(Person)
admin.site.register(DockerImage)
admin.site.register(DockerContainer)
admin.site.register(ClassGroup)
