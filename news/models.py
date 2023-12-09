from django.db import models

from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now

class NewsEntry(models.Model):
    title = models.CharField(max_length=128)
    text = models.TextField()
    pub_date = models.DateTimeField(_("Date"), default=now)
    
    def __str__(self):
        return self.title
