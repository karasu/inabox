""" Challenge app forms go here """

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from .models import Challenge, ProposedSolution, Comment

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

class UploadSolutionForm(forms.ModelForm):
    """ This form is used to upload a challenge solution """
    class Meta:
        """ Django meta class for ModelForm """
        model = ProposedSolution
        fields = ["challenge", "user", "script"]

    def __init__(self, *args, **kwargs):
        user_id = kwargs.pop('user_id', None)
        challenge_id = kwargs.pop('challenge_id', None)
        super().__init__(*args, **kwargs)

        # Add form-control class to all form widgets
        for field in self.visible_fields():
            field.field.widget.attrs.update({'class': 'form-control'})

        if user_id:
            # set the creator field to the current user (and remove the rest)
            self.fields['user'].queryset = User.objects.filter(id=user_id)
            self.fields['user'].empty_label = None

        if challenge_id:
            # set the challenge field to the current challenge (and remove the rest)
            self.fields['challenge'].queryset = Challenge.objects.filter(id=challenge_id)
            self.fields['challenge'].empty_label = None


class SearchForm(forms.Form):
    """ Form used to do a site search """
    search = forms.CharField()


class NewChallengeForm(forms.ModelForm):
    """ Add a new challenge form """
    class Meta:
        """ Django meta class for ModelForm """
        model = Challenge
        fields = [
            "title", "summary", "full_description", "creator",
            "check_solution_script", "area", "level", "points",
            "language", "docker_image"]

    def __init__(self, *args, **kwargs):
        user_id = kwargs.pop('user_id', None)
        super().__init__(*args, **kwargs)

        # Add form-control class to all form widgets
        for field in self.visible_fields():
            field.field.widget.attrs.update({'class': 'form-control'})

        # set the creator field to the current user (and remove the rest)
        if user_id:
            self.fields['creator'].queryset = User.objects.filter(id=user_id)
            self.fields['creator'].empty_label = None

class CommentForm(forms.ModelForm):
    """ Form to add a new comment to a challenge """
    class Meta:
        model = Comment
        fields = ['challenge', 'user', 'body']

    def __init__(self, *args, **kwargs):
        user_id = kwargs.pop('user_id', None)
        challenge_id = kwargs.pop('challenge_id', None)
        super().__init__(*args, **kwargs)

        # Add form-control class to all form widgets
        for field in self.visible_fields():
            field.field.widget.attrs.update({'class': 'form-control'})

        if user_id:
            # set the creator field to the current user (and remove the rest)
            self.fields['user'].queryset = User.objects.filter(id=user_id)
            self.fields['user'].empty_label = None

        if challenge_id:
            # set the challenge field to the current challenge (and remove the rest)
            self.fields['challenge'].queryset = Challenge.objects.filter(id=challenge_id)
            self.fields['challenge'].empty_label = None


class SignUpForm(UserCreationForm):
    """ Form to register a new user """
    class Meta:
        model = User
        fields = ['email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add form-control class to all form widgets
        for field in self.visible_fields():
            field.field.widget.attrs.update({'class': 'form-control'})
