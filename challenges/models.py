from django.db import models

# Create your models here.

class Teacher(models.Model):
    fullname = models.CharField(max_length=256)
    email = models.CharField(max_length=256)
    username = models.CharField(max_length=64)
    avatar = models.ImageField()

    def __str__(self):
        return self.fullname

class Student(models.Model):
    fullname = models.CharField(max_length=256)
    email = models.CharField(max_length=256)
    username = models.CharField(max_length=64)
    avatar = models.ImageField()
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    group = models.CharField(max_length=16)

    def __str__(self):
        return self.fullname

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

class DockerImage(models.Modlel):
    name = models.CharField(max_length=64)
    ssh_port = models.IntegerField()
    limit = models.IntegerField(default=30)
    reuse = models.BooleanField(default=False)
    ports = models.CharField(max_length=256)
    volumes = models.TextField()

    def __str(self):
        return self.name

class Challenge(models.Model):
    title = models.CharField(max_length=256)
    creator = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True) 
    description = models.TextField()
    docker_image = models.ForeignKey(DockerImage, on_delete=models.CASCADE)

    def __str__(self):
        return self.title
