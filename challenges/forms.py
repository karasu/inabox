from django import forms
from django.contrib.auth.models import User

from .models import Challenge, ProposedSolution

class ChallengeSSHForm(forms.Form):
    hostname = forms.CharField(widget=forms.HiddenInput())
    port = forms.IntegerField(widget=forms.HiddenInput())
    username = forms.CharField(widget=forms.HiddenInput())
    password = forms.CharField(widget=forms.HiddenInput())
    privatekey = forms.CharField(widget=forms.HiddenInput(), required=False)
    passphrase = forms.CharField(widget=forms.HiddenInput(), required=False)
    totp = forms.CharField(widget=forms.HiddenInput(), required=False)
    term = forms.CharField(widget=forms.HiddenInput())
    challenge_id = forms.IntegerField(widget=forms.HiddenInput())

class NewChallengeForm(forms.ModelForm):
    class Meta:
        model = Challenge
        fields = [
            "title", "summary", "full_description", "creator",
            "check_solution_script", "area", "level", "points", "language",
            "docker_image"]

    def __init__(self, *args, **kwargs):
        user_id = kwargs.pop('user_id', None)
        super(NewChallengeForm, self).__init__(*args, **kwargs)

        # Add form-control class to all form widgets
        for field in self.visible_fields():
            field.field.widget.attrs.update({'class': 'form-control'})

        # set the creator field to the current user (and remove the rest)
        if user_id:
            self.fields['creator'].queryset = User.objects.filter(id=user_id)
            self.fields['creator'].empty_label = None

class UploadSolutionForm(forms.ModelForm):
    class Meta:
        model = ProposedSolution
        fields = ["challenge", "user", "script"]

    def __init__(self, *args, **kwargs):
        user_id = kwargs.pop('user_id', None)
        challenge_id = kwargs.pop('challenge_id', None)
        super(UploadSolutionForm, self).__init__(*args, **kwargs)

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
