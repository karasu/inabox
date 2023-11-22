from django.db import models

# Create your models here.

from django.db import models

class Teacher(models.Model):
    email = models.CharField(max_length=256)
    username = models.CharField(max_length=64)
    avatar = models.ImageField()
    name = models.CharField(max_length=256)

    def __str__(self):
        return self.name

def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return "user_{0}/{1}".format(instance.user.id, filename)

class User(models.Model):
    email = models.CharField(max_length=256)
    username = models.CharField(max_length=64)
    avatar = models.ImageField(upload_to=user_directory_path)
    name = models.CharField(max_length=256)
    group = models.CharField(max_length=32)
    teacher = models.BooleanField(default=False)
    def __str__(self):
        return self.name



class Challenge(models.Model):
    title = models.CharField(max_length=256)
    creator = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True) 
    description = models.TextField()
    port = models.IntegerField()
    image = models.ImageField()

    def __str__(self):
        return self.title

