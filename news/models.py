from django.db import models

# Create your models here.

from django.db import models


class NewsEntry(models.Model):
    title = models.CharField(max_length=128)
    text = models.TextField()
    pub_date = models.DateTimeField("date published")
