from django import forms
from django.contrib.auth.models import User

from .models import Challenge

class ChallengeSSHForm(forms.Form):
    hostname = forms.CharField(widget=forms.HiddenInput())
    port = forms.IntegerField(widget=forms.HiddenInput())
    username = forms.CharField(widget=forms.HiddenInput())
    password = forms.CharField(widget=forms.HiddenInput())
    privatekey = forms.CharField(widget=forms.HiddenInput(), required=False)
    passphrase = forms.CharField(widget=forms.HiddenInput(), required=False)
    totp = forms.CharField(widget=forms.HiddenInput(), required=False)
    term = forms.CharField(widget=forms.HiddenInput())

class NewChallengeForm(forms.ModelForm):
    class Meta:
        model = Challenge
        fields = [
            "title", "summary", "full_description", "creator", "docker_image",
            "check_script", "area", "level", "points", "language"]

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
