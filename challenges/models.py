import hashlib
import time

from django.utils.timezone import now

from django.db import models
from django.utils.translation import gettext_lazy as _

from Crypto.PublicKey import RSA

try:
    from types import UnicodeType
except ImportError:
    UnicodeType = str

# Create your models here.

# file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
def user_directory_path(instance, filename):
    return "user_{0}/{1}".format(
        instance.user.id, filename)

class ClassGroup(models.Model):
    name = models.CharField(max_length=64)
    description = models.CharField(max_length=256)

    def __str__(self):
        return self.name    

def to_str(bstr, encoding='utf-8'):
    if isinstance(bstr, bytes):
        return bstr.decode(encoding)
    return bstr

def to_bytes(ustr, encoding='utf-8'):
    if isinstance(ustr, UnicodeType):
        return ustr.encode(encoding)
    return ustr

class RSAUtil():
    @staticmethod
    def create_rsa_private_key():
        return to_str(RSA.generate(2048).exportKey())

    @staticmethod
    def get_rsa_public_key(private_key):
        rsa_key = RSA.importKey(to_bytes(private_key))
        return rsa_key.publickey().exportKey()

class Person(models.Model):
    ROLES = [
        ("T", _("Teacher")),
        ("S", _("Student")),
    ]    
    user_name = models.CharField(max_length=64)
    full_name = models.CharField(max_length=256)
    email = models.CharField(max_length=256)
    class_group = models.ForeignKey(
        ClassGroup, on_delete=models.CASCADE)
    role = models.CharField(
        max_length=1, choices=ROLES, default="S")
    teacher = models.ForeignKey(
        'self', on_delete=models.CASCADE)
    avatar = models.ImageField(
        upload_to=user_directory_path, blank=True, null=True)
    private_key = models.TextField(
        default=RSAUtil.create_rsa_private_key())

    def __str__(self):
        return self.full_name
    
    class Meta:
        verbose_name_plural = "people"

#class Institution(models.Model):
#    name = models.CharField(max_length=64)
    

def dockerimage_directory_path(instance, filename):
    return "docker_{0}/{1}".format(
        instance.name, filename)


class DockerImage(models.Model):
    name = models.CharField(max_length=64, unique=True)
    ssh_port = models.IntegerField(default=30000, unique=True)
    # How many containers can be running at the same time
    # from this image
    containers_limit = models.IntegerField(default=30)
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


def challenge_directory_path(instance, filename):
    return "challenge_{0}/{1}".format(
        instance.title, filename)

class Area(models.Model):
    name = models.CharField(max_length=256)
    description = models.TextField()

    def __str__(self):
        return self.name

class Challenge(models.Model):
    LEVELS = [
        ("N", _("Novice")),
        ("A", _("Advanced Beginner")),
        ("C", _("Competent")),
        ("P", _("Proficient")),
        ("E", _("Expert")),
    ]   
    title = models.CharField(max_length=256, unique=True)
    creator = models.ForeignKey(
        Person, on_delete=models.CASCADE)
    pub_date = models.DateTimeField(
        _("Date"), default=now)
    summary = models.TextField()
    full_description = models.TextField()
    docker_image = models.ForeignKey(
        DockerImage, on_delete=models.CASCADE, verbose_name="Docker image")
    check_script = models.FileField(_("Script"), 
        upload_to=challenge_directory_path
    )
    approved = models.BooleanField(default=False)
    tries = models.IntegerField(default=0)
    solved = models.IntegerField(default=0)
    area = models.ForeignKey(
        Area, on_delete=models.CASCADE, verbose_name="Area")
    difficulty = models.CharField(
        max_length=1, choices=LEVELS, default="N")

    def __str__(self):
        return self.title

class DockerContainer(models.Model):
    container_id = models.CharField(
        max_length=128, default="0")
    challenge = models.ForeignKey(
        Challenge, on_delete=models.CASCADE)
    user = models.ForeignKey(
        Person, on_delete=models.CASCADE)

    def __str__(self):
        return self.container_id
