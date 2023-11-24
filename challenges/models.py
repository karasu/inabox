from django.db import models

# Create your models here.

def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return "user_{0}/{1}".format(
        instance.user.id, filename)

class User(models.Model):    
    username = models.CharField(max_length=64)
    fullname = models.CharField(max_length=256)
    email = models.CharField(max_length=256)
    group = models.CharField(
        max_length=32, blank=True, default='')
    is_teacher = models.BooleanField(default=False)
    teacher = models.ForeignKey(
        'self', on_delete=models.CASCADE, blank=True, null=True)
    avatar = models.ImageField(upload_to=user_directory_path, blank=True, null=True)

    def __str__(self):
        return self.fullname

def docker_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/docker_<id>/<filename>
    return "docker_{0}/{1}".format(
        instance.docker_image.id, filename)

class DockerImage(models.Model):
    name = models.CharField(max_length=64)
    ssh_port = models.IntegerField(default=30000)
    limit = models.IntegerField(default=30)
    reuse = models.BooleanField(default=False)
    ports = models.CharField(max_length=256, blank=True, default='')
    volumes = models.TextField(blank=True, default='')
    dockerfile = models.FileField(
        upload_to=docker_directory_path)
    docker_image = models.FileField(
        upload_to=docker_directory_path, blank=True, default='')

    def __str__(self):
        return self.name

class Challenge(models.Model):
    title = models.CharField(max_length=256)
    creator = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True)
    pub_date = models.DateTimeField("date published")
    description = models.TextField()
    docker_image = models.ForeignKey(DockerImage, on_delete=models.CASCADE)

    def __str__(self):
        return self.title
