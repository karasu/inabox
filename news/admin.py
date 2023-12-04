from django.contrib import admin

# Register your models here.

from .models import NewsEntry

admin.site.register(NewsEntry)
