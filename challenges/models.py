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
        Teacher,
        on_delete=models.CASCADE,
        primary_key=True) 
    description = models.TextField()
    docker_image = models.ForeignKey(DockerImage, on_delete=models.CASCADE)

    def __str__(self):
        return self.title
