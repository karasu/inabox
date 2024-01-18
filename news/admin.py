""" Register your models here """

from django.contrib import admin

from .models import NewsEntry

admin.site.register(NewsEntry)
