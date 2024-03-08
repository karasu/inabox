""" Challenge app forms go here """

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from .models import Challenge, ProposedSolution, Comment, Profile

class InaboxModelForm(forms.ModelForm):
    """ Base form class for forms based on ModelForm """
    def __init__(self, *args, **kwargs):
        user_id = kwargs.pop('user_id', None)
        challenge_id = kwargs.pop('challenge_id', None)
        super().__init__(*args, **kwargs)

        # Add form-control class to all form widgets
        for field in self.visible_fields():
            if isinstance(field.field, forms.fields.BooleanField):
                field.field.widget.attrs.update({'class': 'form-check-input form-switch'})
            elif isinstance(field.field, forms.fields.DateTimeField):
                field.field.widget.attrs.update({'class': ''})
            else:
                field.field.widget.attrs.update({'class': 'form-control'})
    
        if user_id:
            # set the creator field to the current user (and remove the rest)
            self.fields['user'].queryset = User.objects.filter(id=user_id)
            self.fields['user'].empty_label = None
            self.fields['user'].disabled = True

        if challenge_id:
            # set the challenge field to the current challenge (and remove the rest)
            self.fields['challenge'].queryset = Challenge.objects.filter(id=challenge_id)
            self.fields['challenge'].empty_label = None
            self.fields['challenge'].disabled = True


class ChallengeSSHForm(forms.Form):
    """ Form with ssh connection data """
    hostname = forms.CharField(widget=forms.HiddenInput())
    port = forms.IntegerField(widget=forms.HiddenInput())
    username = forms.CharField(widget=forms.HiddenInput())
    password = forms.CharField(widget=forms.HiddenInput())
    privatekey = forms.CharField(widget=forms.HiddenInput(), required=False)
    passphrase = forms.CharField(widget=forms.HiddenInput(), required=False)
    totp = forms.CharField(widget=forms.HiddenInput(), required=False)
    term = forms.CharField(widget=forms.HiddenInput())
    challenge_id = forms.IntegerField(widget=forms.HiddenInput())
    image_name = forms.CharField(widget=forms.HiddenInput(), required=False)
    container_id = forms.CharField(widget=forms.HiddenInput(), required=False)

class StartAgainForm(forms.Form):
    """ Form with challenge and container info """
    challenge_id = forms.IntegerField(widget=forms.HiddenInput())
    image_name = forms.CharField(widget=forms.HiddenInput(), required=False)
    container_id = forms.CharField(widget=forms.HiddenInput(), required=False)

class UploadSolutionForm(InaboxModelForm):
    """ This form is used to upload a challenge solution """
    class Meta:
        """ Django meta class for ModelForm """
        model = ProposedSolution
        fields = ["challenge", "user", "script"]


class SearchForm(forms.Form):
    """ Form used to do a site search """
    search = forms.CharField()


class NewChallengeForm(InaboxModelForm):
    """ Add a new challenge form """
    class Meta:
        """ Django meta class for ModelForm """
        model = Challenge
        fields = [
            "title", "summary", "full_description", "creator",
            "check_solution_script", "area", "level", "points",
            "language", "docker_image"]


class CommentForm(InaboxModelForm):
    """ Form to add a new comment to a challenge """
    class Meta:
        model = Comment
        fields = ['challenge', 'user', 'body']


class SignUpForm(UserCreationForm):
    """ Form to register a new user """
    class Meta:
        model = User
        fields = ['username', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add form-control class to all form widgets
        for field in self.visible_fields():
            field.field.widget.attrs.update({'class': 'form-control'})

class UserForm(InaboxModelForm):
    """ Used to edit certain user's fields when modifying user's profile """
    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email', 'is_active',
            'is_superuser', 'is_staff', 'last_login', 'date_joined']
    disable = [
        'username', 'is_active', 'is_superuser', 'is_staff',
        'last_login', 'date_joined']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # disable these fields
        for field_name in self.disable:
            self.fields[field_name].disabled = True    


class ProfileForm(InaboxModelForm):
    """ Edit user's profile form """
    class Meta:
        model = Profile
        fields = [
            'user', 'class_group', 'role', 'teacher', 'avatar',
            'language', 'points', 'team', 'organization', 'private_key']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user'].disabled = True
