from django.db import models

from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now
# Get available languages
from django.conf import settings


class NewsEntry(models.Model):
    title = models.CharField(max_length=128)
    text = models.TextField()
    pub_date = models.DateField(_("Date"), default=now)
    language = models.CharField(
        choices=settings.LANGUAGES, max_length=2, default="ca")

    class Meta:
        verbose_name_plural = "news entries"

    def __str__(self):
        return self.title
