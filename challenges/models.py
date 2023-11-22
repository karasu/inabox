from django.db import models

# Create your models here.

from django.db import models


#class Question(models.Model):
#    question_text = models.CharField(max_length=200)
#    pub_date = models.DateTimeField("date published")


#class Choice(models.Model):
#    question = models.ForeignKey(Question, on_delete=models.CASCADE)
#    choice_text = models.CharField(max_length=200)
#    votes = models.IntegerField(default=0)


class Challenge(models.Model):
    title = models.CharField(max_length=200)
    creator = models.OneToOneField(
        Teacher,
        on_delete=models.CASCADE,
        primary_key=True) 
    description = models.TextField()
    port = models.IntegerField()

class Teacher(models.Model):
    email = models.CharField(max_length=200)
    username = models.CharField(max_length=64)
    avatar = models.ImageField()

class Student(models.Model):
    email = models.CharField(max_length=200)
    username = models.CharField(max_length=64)
    avatar = models.ImageField()
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
