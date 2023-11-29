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


def dockerimage_directory_path(instance, filename):
    return "docker_{0}/{1}".format(
        instance.hash, filename)


class DockerImage(models.Model):
    name = models.CharField(max_length=64, unique=True)
    ssh_port = models.IntegerField(default=30000, unique=True)
    # How many containers can be running at the same time
    # from this image
    conatiners_limit = models.IntegerField(default=30)
    # If there is already one container running, use it instead
    # of creating a new one. This should be always false as it is now.
    reuse_container = models.BooleanField(default=False)
    # docker file used to generate this docker image
    docker_file = models.FileField(
        upload_to=dockerimage_directory_path)
    # (when the docker image is generated, its id will be stored here
    docker_image_id = models.CharField(
        max_length=12, default="0")
    # optional docker parameters
    optional_docker_ports = models.CharField(max_length=256, blank=True, default='')
    optional_docker_volumes = models.TextField(blank=True, default='')
    
    def __str__(self):
        return self.name


class DockerContainer(models.Model):
    container_id = models.CharField(
        max_length=128, default="0")
    challenge = models.ForeignKey(
        'Challenge', on_delete=models.CASCADE, blank=True, null=True)
    user = models.ForeignKey(
        'User', on_delete=models.CASCADE, blank=True, null=True)


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
