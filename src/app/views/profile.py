""" Profile view """

from django.views import generic
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.mixins import LoginRequiredMixin

from ..models import Profile
from ..models import ROLES
from ..forms import ProfileForm

'''
class ProfileView(LoginRequiredMixin, generic.base.TemplateView):
    """ Show user's profile """
    template_name = "app/profile.html"
    editMode = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['roles'] = ROLES
        context['editMode'] = self.editMode

        objs = {
            "user": User.objects.get(id=self.request.user.id),
            "profile": Profile.objects.get(user=self.request.user)
        }

        excludes = {
            "user": ["id", "password", "groups", "user_permissions", "profile"],
            "profile": ["id", "user", "private_key", "challenge",
                "proposedsolution", "quest", "logentry"]}

        for k, obj in objs.items():
            name = k + "_data"
            context[name] = []
            for field in obj._meta.get_fields():
                if field.name not in excludes[k]:
                    item = self.get_field_data(obj, field)
                    if item:
                        context[name].append(item)

        return context

    def get_field_data(self, obj, field):
        """ gets field label and value """

        try:
            label = field.verbose_name.capitalize()
            value = field.value_from_object(obj)
            input_type = "text"
            class_value = "form-control"

            #if field.name == "avatar":
            # input_type = "file"
            #    #class_value = "form-control-file"

            if field.name == "email":
                input_type = "email"

            if field.name == "teacher":
                value = User.objects.get(id=value)

            if field.name == "role":
                for (myid, desc) in ROLES:
                    if myid == value:
                        value = desc

            if field.name == "class_group":
                value = ClassGroup.objects.get(id=value)

            if field.name == "language":
                lang_info = get_language_info(value)
                value = lang_info["name_translated"]

            if field.name == "team":
                value = Team.objects.get(id=value)

            if field.name == "organization":
                value = Organization.objects.get(id=value)

            if value is True:
                value = _("Yes")
            elif value is False:
                value = _("No")

            return {
                "name": field.name,
                "label": label,
                "value": value,
                "type": input_type,
                "class": class_value,
            }
        except AttributeError as err:
            print(err)
            return None

    def post(self, request, *args, **kwargs):
        """ Activate edition or save changes """
        pass
'''

class ProfileView(LoginRequiredMixin, generic.DetailView):
    """ Show user's profile """
    template_name = "app/profile.html"
    model = Profile
    editMode = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['roles'] = ROLES
        context['editMode'] = self.editMode
        #user.id
        context['form'] = ProfileForm()

        #value = Team.objects.get(id=value)

        return context
