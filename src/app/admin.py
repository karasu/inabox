""" Register models in the admin module """

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
#from django.contrib.auth.models import User

# Register your models here.

from .models import Challenge
from .models import Quest
from .models import DockerImage
from .models import Area
from .models import ClassGroup
from .models import Profile
from .models import ProposedSolution
from .models import Team
from .models import Organization
from .models import Comment
from .models import NewsEntry
from .models import InaboxUser

admin.site.register(Challenge)
admin.site.register(Quest)
admin.site.register(Area)
admin.site.register(DockerImage)
admin.site.register(ClassGroup)
admin.site.register(ProposedSolution)
admin.site.register(Team)
admin.site.register(Organization)
admin.site.register(NewsEntry)

class CommentAdmin(admin.ModelAdmin):
    """ Admin challenge's comments """
    list_display = ('user', 'body', 'challenge', 'created_on', 'active')
    list_filter = ('active', 'created_on')
    search_fields = ('user', 'email', 'body')
    actions = ['approve_comments']

    def approve_comments(self, request, queryset):
        """ Set active to True to approve comment """
        queryset.update(active=True)
admin.site.register(Comment, CommentAdmin)

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
#admin.site.unregister(User)
admin.site.register(InaboxUser, UserAdmin)
