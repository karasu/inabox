""" Models module """

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

# Used in profile model
ROLES = [
    ("T", _("Teacher")),
    ("S", _("Student")),
]

def to_str(bstr, encoding='utf-8'):
    """ Converts bytes to string """
    if isinstance(bstr, bytes):
        return bstr.decode(encoding)
    return bstr

def to_bytes(ustr, encoding='utf-8'):
    """ Converts string to bytes """
    if isinstance(ustr, UnicodeType):
        return ustr.encode(encoding)
    return ustr


class RSAUtil():
    """ RSA helper class """

    @staticmethod
    def create_rsa_private_key():
        """ Get the RSA private key """
        return to_str(RSA.generate(2048).exportKey())

    @staticmethod
    def get_rsa_public_key(private_key):
        """ Get the RSA public key """
        rsa_key = RSA.importKey(to_bytes(private_key))
        return rsa_key.publickey().exportKey()


def user_directory_path(instance, filename):
    """ file will be uploaded to MEDIA_ROOT/users/<username>/<filename> """
    return f"users/{instance.user.username}/{filename}"

class ClassGroup(models.Model):
    """ Store class here """
    name = models.CharField(max_length=64)
    description = models.CharField(max_length=256)

    def __str__(self):
        return str(self.name)


def teams_directory_path(instance, filename):
    """ returns teams directory """
    return f"teams/{instance.name}/{filename}"

class Team(models.Model):
    """ Store player team """
    name = models.CharField(max_length=128, unique=True)
    image = models.ImageField(
        upload_to=teams_directory_path,
        default="challenges/images/avatars/256x256/028.jpg")
    description = models.TextField()

    def __str__(self):
        return str(self.name)


def organizations_directory_path(instance, filename):
    """ returns organizations directory """
    return f"organizations/{instance.name}/{filename}"

class Organization(models.Model):
    """ Store the organization to which the player belongs to """
    name = models.CharField(max_length=128, unique=True)
    image = models.ImageField(
        upload_to=organizations_directory_path,
        default="challenges/images/avatars/256x256/029.jpg")
    description = models.TextField()

    def __str__(self):
        return str(self.name)


class Profile(models.Model):
    """ Store users' profile """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    class_group = models.ForeignKey(
        ClassGroup, on_delete=models.CASCADE)
    role = models.CharField(
        max_length=1, choices=ROLES, default="S")
    teacher = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="teacher",
        verbose_name=_("Teacher"))
    avatar = models.ImageField(
        upload_to=user_directory_path,
        default="challenges/images/avatars/256x256/021.jpg")
    private_key = models.TextField(
        default=RSAUtil.create_rsa_private_key())
    language = models.CharField(
        choices=settings.LANGUAGES, max_length=2, default="ca")
    points = models.IntegerField(default=0)
    team = models.ForeignKey(
        Team, default=1, on_delete=models.CASCADE)
    organization = models.ForeignKey(
        Organization, default=1, on_delete=models.CASCADE)

    def calculate_solved_challenges(self):
        """ calc how many solved challenges the user has done """
        return ProposedSolution.objects.filter(
            user=self.user, is_solved=True).count()
    solved = property(calculate_solved_challenges)

    def __str__(self):
        return f"{self.user.username}'s profile"


# file will be uploaded to MEDIA_ROOT/dockerimages/<dockerimagename>/<filename>
def dockerimage_directory_path(instance, filename):
    """ get dockerimage directory """
    return f"dockerimages/{instance.name}/{filename}"

class DockerImage(models.Model):
    """ Store a docker image information """
    # This name is what will be shown to the user
    # (it can be different from the real image name)
    name = models.CharField(
        max_length=64, unique=True)
    # data to connect to the docker container
    container_ssh_port = models.IntegerField(
        default=30000, unique=True)
    container_username = models.CharField(
        max_length=64, default="inabox")
    container_password = models.CharField(
        max_length=64, default="aW5hYm94")
    container_privatekey = models.TextField()
    container_passphrase = models.CharField(
        max_length=256)

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
    optional_docker_ports = models.CharField(
        max_length=256, blank=True, default='')
    optional_docker_volumes = models.TextField(
        blank=True, default='')

    def __str__(self):
        return str(self.name)


class Area(models.Model):
    """ Store challenge's area """
    name = models.CharField(max_length=256)
    description = models.TextField()

    def __str__(self):
        return str(self.name)


def challenge_directory_path(instance, filename):
    """ file will be uploaded to MEDIA_ROOT/challenges/<challengetitle>/<filename> """
    return f"challenges/{instance.title}/{filename}"

class Challenge(models.Model):
    """ Store challenge """
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
    solved = models.IntegerField(default=0)
    area = models.ForeignKey(
        Area, on_delete=models.CASCADE, verbose_name="Area")
    level = models.CharField(
        max_length=1, choices=LEVELS, default="N")
    points = models.IntegerField(default=0)
    language = models.CharField(
        choices=settings.LANGUAGES, max_length=2, default="ca")

    def __str__(self):
        return str(self.title)


class UserChallengeContainer(models.Model):
    """ Store docker container's info """
    container_id = models.CharField(
        max_length=128, default="0")
    challenge = models.ForeignKey(
        Challenge, on_delete=models.CASCADE)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.container_id)

def user_solutions_path(instance, filename):
    """ file will be uploaded to MEDIA_ROOT/solutions/<username>/<challengetitle> """
    return f"solutions/{instance.user.username}/{instance.challenge.title}/{filename}"

class ProposedSolution(models.Model):
    """ Stores each user's solution to each challenge """
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
        return f"{self.challenge} tried by {self.user}"


class Quest(models.Model):
    """ Quests are challenge collections that have some connection between them """
    title = models.CharField(max_length=256, unique=True)
    summary = models.TextField()
    creator = models.ForeignKey(
        User, on_delete=models.CASCADE)
    pub_date = models.DateTimeField(
        _("Date"), default=now)
    total_tries = models.IntegerField(default=0)
    solved = models.IntegerField(default=0)
    level = models.CharField(
        max_length=1, choices=LEVELS, default='N')

    def __str__(self):
        return str(self.title)


class QuestChallenge(models.Model):
    """ # Store the list of challenges that are part of a Quest """
    quest = models.ForeignKey(
        Quest, on_delete=models.CASCADE)
    challenge = models.ForeignKey(
        Challenge, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.quest} - {self.challenge}"
