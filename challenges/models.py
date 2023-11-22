from django.db import models

# Create your models here.

class Teacher(models.Model):
    email = models.CharField(max_length=200)
    username = models.CharField(max_length=64)
    avatar = models.ImageField()

class Student(models.Model):
    email = models.CharField(max_length=200)
    username = models.CharField(max_length=64)
    avatar = models.ImageField()
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)

class DockerImage(models.Modlel):
    name = models.CharField(max_length=64)
    ssh_port = models.IntegerField()
    limit = models.IntegerField(default=30)
    reuse = models.BooleanField(default=False)
    ports = models.CharField(max_length=256)
    volumes = models.TextField()

class Challenge(models.Model):
    title = models.CharField(max_length=200)
    creator = models.OneToOneField(
        Teacher(),
        on_delete=models.CASCADE,
        primary_key=True) 
    description = models.TextField()
    docker_image = models.ForeignKey(DockerImage, on_delete=models.CASCADE)

