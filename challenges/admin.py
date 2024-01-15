from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User


# Register your models here.

from .models import Challenge
from .models import DockerImage
from .models import DockerContainer
from .models import Area
from .models import ClassGroup
from .models import Profile
from .models import ProposedSolution
from .models import Team
from .models import Organization

admin.site.register(Challenge)
admin.site.register(Area)
admin.site.register(DockerImage)
admin.site.register(DockerContainer)
admin.site.register(ClassGroup)
admin.site.register(ProposedSolution)
admin.site.register(Team)
admin.site.register(Organization)


class ProfileInline(admin.StackedInline):
    """ Define an inline admin descriptor for Profile model
    which acts a bit like a singleton """
    model = Profile
    can_delete = False
    verbose_name_plural = "profiles"
    fk_name = "user"


class UserAdmin(BaseUserAdmin):
    """ Define a new User admin """
    inlines = [ProfileInline]


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
