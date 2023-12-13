from django import forms


class ConnectForm(forms.Form):
    hostname = forms.CharField(widget=forms.HiddenInput(), initial="localhost")
    port = forms.IntegerField(widget=forms.HiddenInput(), initial=30001)
    username = forms.CharField(widget=forms.HiddenInput(), initial="inabox")
    password = forms.CharField(widget=forms.HiddenInput(), initial="aW5hYm94Cg==")
    privatekey = forms.CharField(widget=forms.HiddenInput(), required=False)
    passphrase = forms.CharField(widget=forms.HiddenInput(), required=False)
    totp = forms.CharField(widget=forms.HiddenInput(), required=False)
    term = forms.CharField(widget=forms.HiddenInput(), initial="xterm-256color")
