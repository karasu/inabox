import hashlib
import time

from django.utils.timezone import now

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User

# Get available languages
from django.conf import settings

try:
    from Crypto.PublicKey import RSA
except ModuleNotFoundError:
    # Debian
    from Cryptodome.PublicKey import RSA

try:
    from types import UnicodeType
except ImportError:
    UnicodeType = str

# Create your models here.

# Used in Challenge and Quest models
LEVELS = [
    ("N", _("Novice")),
    ("A", _("Advanced Beginner")),
    ("C", _("Competent")),
    ("P", _("Proficient")),
    ("E", _("Expert")),
]

# file will be uploaded to MEDIA_ROOT/users/<username>/<filename>
def user_directory_path(instance, filename):
    return "users/{0}/{1}".format(
        instance.user.username, filename)

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


'''
Django user has this fields:
    username
    password
    email
    first_name
    last_name
'''

'''
usr = User.objects.get(username="fsmith")
freds_role = usr.profile.role
'''

class Profile(models.Model):
    ROLES = [
        ("T", _("Teacher")),
        ("S", _("Student")),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)    
    class_group = models.ForeignKey(
        ClassGroup, on_delete=models.CASCADE)
    role = models.CharField(
        max_length=1, choices=ROLES, default="S")
    teacher = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="teacher",
        verbose_name=_("Teacher"))
    avatar = models.ImageField(
        upload_to=user_directory_path, blank=True, null=True)
    private_key = models.TextField(
        default=RSAUtil.create_rsa_private_key())
    language = models.CharField(
        choices=settings.LANGUAGES, max_length=2, default="ca")

    def __str__(self):
        return "{}'s profile".format(self.user.username)
    
# file will be uploaded to MEDIA_ROOT/dockerimages/<dockerimagename>/<filename>
def dockerimage_directory_path(instance, filename):
    return "dockerimages/{0}/{1}".format(
        instance.name, filename)

class DockerImage(models.Model):
    # This name is what will be shown to the user (it can be different from the real image name)
    name = models.CharField(max_length=64, unique=True)
    # data to connect to the docker container
    container_ssh_port = models.IntegerField(default=30000, unique=True)
    container_username = models.CharField(max_length=64, default="inabox")
    container_password = models.CharField(max_length=64, default="aW5hYm94")
    container_privatekey = models.TextField()
    container_passphrase = models.CharField(max_length=256)

    # How many containers can be running at the same time
    # from this image
    containers_limit = models.IntegerField(default=30)
    # If there is already one container running, use it instead
    # of creating a new one. This should be always false as it is now.
    reuse_container = models.BooleanField(default=False)
    # docker file used to generate this docker image
    docker_file = models.FileField(
        upload_to=dockerimage_directory_path)
    # docker image name in Docker
    docker_name = models.CharField(max_length=64)
    # optional docker parameters
    optional_docker_ports = models.CharField(max_length=256, blank=True, default='')
    optional_docker_volumes = models.TextField(blank=True, default='')
    
    def __str__(self):
        return self.name


class Area(models.Model):
    name = models.CharField(max_length=256)
    description = models.TextField()

    def __str__(self):
        return self.name


# file will be uploaded to MEDIA_ROOT/challenges/<challengetitle>/<filename>
def challenge_directory_path(instance, filename):
    return "challenges/{0}/{1}".format(
        instance.title, filename)

class Challenge(models.Model):
    title = models.CharField(max_length=256, unique=True)
    creator = models.ForeignKey(
        User, on_delete=models.CASCADE)
    pub_date = models.DateTimeField(
        _("Date"), default=now)
    summary = models.TextField()
    full_description = models.TextField()
    docker_image = models.ForeignKey(
        DockerImage, on_delete=models.CASCADE, verbose_name="Docker image")
    check_solution_script = models.FileField(
        verbose_name="Script", upload_to=challenge_directory_path)
    approved = models.BooleanField(default=False)
    total_tries = models.IntegerField(default=0)
    times_solved = models.IntegerField(default=0)
    area = models.ForeignKey(
        Area, on_delete=models.CASCADE, verbose_name="Area")
    level = models.CharField(
        max_length=1, choices=LEVELS, default="N")
    points = models.IntegerField(default=1)
    language = models.CharField(
        choices=settings.LANGUAGES, max_length=2, default="ca")

    def __str__(self):
        return self.title


class DockerContainer(models.Model):
    container_id = models.CharField(
        max_length=128, default="0")
    challenge = models.ForeignKey(
        Challenge, on_delete=models.CASCADE)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE)

    def __str__(self):
        return self.container_id


# file will be uploaded to MEDIA_ROOT/solutions/<username>/<challengetitle>
def user_solutions_path(instance, filename):
    return "solutions/{0}/{1}/{2}".format(
        instance.user.username,
        instance.challenge.title,
        filename)


# Stores each user's solution to each challenge
class ProposedSolution(models.Model):
    challenge = models.ForeignKey(
        Challenge, on_delete=models.CASCADE)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE)
    script = models.FileField(
        upload_to=user_solutions_path,
        verbose_name='Solution script')
    tries = models.IntegerField(default=1)
    is_tested = models.BooleanField(default=False)
    is_solved = models.BooleanField(default=False)
    last_test_result = models.TextField()

    def __str__(self):
        return "{} tried by {}".format(self.challenge, self.user)


# Quests are challenge collections that have some connection between them
class Quest(models.Model):
    title = models.CharField(max_length=256, unique=True)
    summary = models.TextField()
    creator = models.ForeignKey(
        User, on_delete=models.CASCADE)
    pub_date = models.DateTimeField(
        _("Date"), default=now)
    total_tries = models.IntegerField(default=0)
    times_solved = models.IntegerField(default=0)
    level = models.CharField(
        max_length=1, choices=LEVELS, default='N')
    
    def __str__(self):
        return self.title


# So we can store the list of challenges that are part of a Quest
class QuestChallenge(models.Model):
    quest = models.ForeignKey(
        Quest, on_delete=models.CASCADE)
    challenge = models.ForeignKey(
        Challenge, on_delete=models.CASCADE)

    def __str__(self):
        return "{} - {}".format(self.quest, self.challenge)
