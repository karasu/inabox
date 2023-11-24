import hashlib
import time

from django.db import models
from django.utils.translation import gettext_lazy as _

# Create your models here.

# file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
def user_directory_path(instance, filename):
    return "user_{0}/{1}".format(
        instance.user.id, filename)


class User(models.Model):
    ROLES = [
        ("T", _("Teacher")),
        ("S", _("Student")),
    ]    
    user_name = models.CharField(max_length=64)
    full_name = models.CharField(max_length=256)
    email = models.CharField(max_length=256)
    group = models.CharField(
        max_length=32, blank=True, default='')
    role = models.CharField(
        max_length=1, choices=ROLES, default="S")
    teacher = models.ForeignKey(
        'self', on_delete=models.CASCADE, blank=True, null=True)
    avatar = models.ImageField(
        upload_to=user_directory_path, blank=True, null=True)

    def __str__(self):
        return self.full_name


# Generate 10 character long hash
def createHash():
    hash = hashlib.sha1()
    hash.update(str(time.time()).encode('utf-8'))
    return hash.hexdigest()

def dockerimage_directory_path(instance, filename):
    return "docker_{0}/{1}".format(
        instance.hash, filename)


class DockerImage(models.Model):
    name = models.CharField(max_length=64)
    ssh_port = models.IntegerField(default=30000, unique=True)
    limit = models.IntegerField(default=30)
    reuse = models.BooleanField(default=False)
    ports = models.CharField(max_length=256, blank=True, default='')
    volumes = models.TextField(blank=True, default='')
    docker_file = models.FileField(
        upload_to=dockerimage_directory_path)
    docker_image = models.FileField(
        upload_to=dockerimage_directory_path, blank=True, default='')
    hash = models.CharField(
        max_length=128, default=createHash)
    
    def __str__(self):
        return self.name


class Challenge(models.Model):
    title = models.CharField(max_length=256)
    creator = models.ForeignKey(
        User, on_delete=models.CASCADE)
    pub_date = models.DateTimeField("date published")
    description = models.TextField()
    docker_image = models.ForeignKey(
        DockerImage, on_delete=models.CASCADE)

    def __str__(self):
        return self.title
